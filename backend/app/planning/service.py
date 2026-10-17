"""Weekly occurrences are snapshots; templates only generate missing weeks."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from beanie import PydanticObjectId as ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from base.task_timing import TASK_TIMEZONE, scheduled_datetime, task_deadline, utc_datetime
from models.models import Board, PlanEntry, PlanTemplate, Task


HORIZON_WEEKS = 2  # Current week and the next two weeks.
CONTENT_FIELDS = ("kind", "title", "description", "time", "end_time", "board_id")


def monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def today(now=None) -> date:
    return utc_datetime(now or datetime.now(timezone.utc)).astimezone(TASK_TIMEZONE).date()


def collection(model):
    return model.get_pymongo_collection()


async def documents(model, query):
    return await collection(model).find(query).to_list(length=None)


def public(document):
    return {**document, "_id": str(document["_id"])}


async def get_entry(user, entry_id):
    if not ObjectId.is_valid(entry_id):
        raise HTTPException(422, "Invalid plan entry ID")
    entry = await collection(PlanEntry).find_one({"_id": ObjectId(entry_id), "user": user})
    if entry is None:
        raise HTTPException(404, "Plan entry not found")
    return entry


async def quest_for(entry):
    return await collection(Task).find_one({"user": entry["user"], "plan_entry_id": str(entry["_id"])})


async def entry_completed(entry):
    quest = await quest_for(entry) if entry.get("board_id") else None
    return quest.get("completed", False) if quest else entry.get("completed", False)


async def validate_links(user, data, week):
    board = None
    goal = None
    if data.board_id:
        board = await collection(Board).find_one({"_id": ObjectId(data.board_id), "username": user})
        if board is None:
            raise HTTPException(404, "Board not found")
    if data.goal_id:
        goal = await get_entry(user, data.goal_id)
        if goal["kind"] != "goal" or goal["week_start"] != week or goal.get("cancelled"):
            raise HTTPException(422, "Choose an active goal from the same week")
        if data.repeat and not goal.get("template_id"):
            raise HTTPException(422, "A repeating task requires a repeating goal")
    return board, goal


async def upsert_occurrence(fields):
    query = {"series_id": fields["series_id"], "week_start": fields["week_start"]}
    document = PlanEntry.model_validate({"_id": ObjectId(), **fields}).model_dump(by_alias=True)
    try:
        await collection(PlanEntry).update_one(query, {"$setOnInsert": document}, upsert=True)
    except DuplicateKeyError:
        # Another request/worker generated this same occurrence concurrently.
        pass
    return await collection(PlanEntry).find_one(query)


async def sync_quest(entry, now=None):
    """One quest per occurrence. Future quests remain hidden by Task.date."""
    now = utc_datetime(now or datetime.now(timezone.utc))
    query = {"plan_entry_id": str(entry["_id"]), "user": entry["user"]}
    if entry.get("cancelled"):
        await collection(Task).update_many(query, {"$set": {"inactive": True}})
        return
    if not entry.get("board_id"):
        await collection(Task).delete_many({**query, "completed": False})
        return
    board = await collection(Board).find_one({"_id": ObjectId(entry["board_id"]), "username": entry["user"]})
    if board is None:
        return
    start = scheduled_datetime(datetime.fromisoformat(entry["day"]))
    deadline = task_deadline(start, board.get("task_expire_days"))
    fields = dict(
        title=entry["title"], description=entry.get("description", ""),
        board_id=entry["board_id"], date=start,
        inactive=deadline is not None and now >= deadline,
    )
    existing = await collection(Task).find_one(query)
    if existing:
        await collection(Task).update_one(
            {**query, "completed": False}, {"$set": fields},
        )
    else:
        quest = Task.model_validate(dict(
            _id=ObjectId(), user=entry["user"], plan_entry_id=str(entry["_id"]),
            created_at=now, **fields,
        )).model_dump(by_alias=True)
        try:
            await collection(Task).update_one(query, {"$setOnInsert": quest}, upsert=True)
        except DuplicateKeyError:
            pass


async def materialize_template(template, week, now=None):
    day = week + timedelta(days=template["weekday"] if template["kind"] == "task" else 0)
    if day.isoformat() < template["starts_on"]:
        return
    if template.get("ends_before") and day.isoformat() >= template["ends_before"]:
        return
    goal = None
    if template.get("goal_template_id"):
        goal = await collection(PlanEntry).find_one({
            "user": template["user"], "template_id": template["goal_template_id"],
            "week_start": week.isoformat(), "cancelled": False,
        })
    board = None
    if template.get("board_id"):
        board = await collection(Board).find_one({"_id": ObjectId(template["board_id"]), "username": template["user"]})
    entry = await upsert_occurrence(dict(
        **{key: template.get(key) for key in CONTENT_FIELDS},
        user=template["user"], week_start=week.isoformat(), day=day.isoformat(),
        template_id=str(template["_id"]), series_id=template.get("series_id") or str(template["_id"]),
        goal_id=str(goal["_id"]) if goal else None,
        board_title=board["title"] if board else None,
    ))
    if entry["kind"] == "task":
        await sync_quest(entry, now)


async def refresh(user=None, now=None):
    """Catch up missed weeks and keep only a finite future horizon prepared."""
    now = utc_datetime(now or datetime.now(timezone.utc))
    horizon = monday(today(now)) + timedelta(weeks=HORIZON_WEEKS)
    query = {"starts_on": {"$lte": (horizon + timedelta(days=6)).isoformat()}}
    if user is not None:
        query["user"] = user
    templates = await documents(PlanTemplate, query)
    # Goals must exist before their parts are generated.
    templates.sort(key=lambda template: template["kind"] != "goal")
    for template in templates:
        week = monday(date.fromisoformat(template["starts_on"]))
        if template.get("generated_through"):
            week = max(week, date.fromisoformat(template["generated_through"]) + timedelta(weeks=1))
        while week <= horizon:
            await materialize_template(template, week, now)
            # $max avoids moving the cursor backwards during concurrent refreshes.
            await collection(PlanTemplate).update_one(
                {"_id": template["_id"]}, {"$max": {"generated_through": week.isoformat()}},
            )
            week += timedelta(weeks=1)
    # Repair an interrupted quest creation without re-generating historical rows.
    repair_query = {
        "kind": "task", "board_id": {"$type": "string"},
        "week_start": {"$gte": (monday(today(now)) - timedelta(weeks=1)).isoformat(), "$lte": horizon.isoformat()},
    }
    if user is not None:
        repair_query["user"] = user
    for entry in await documents(PlanEntry, repair_query):
        await sync_quest(entry, now)


async def prepare_week(user, week, now=None):
    await refresh(user, now)
    # An explicitly opened future week can be edited without generating all intervening weeks.
    if week > monday(today(now)) + timedelta(weeks=HORIZON_WEEKS):
        templates = await documents(PlanTemplate, {"user": user})
        templates.sort(key=lambda template: template["kind"] != "goal")
        for template in templates:
            await materialize_template(template, week, now)


async def get_week(user, day=None, now=None):
    week = monday(day or today(now))
    await prepare_week(user, week, now)
    entries = await documents(PlanEntry, {"user": user, "week_start": week.isoformat()})
    quests = await documents(Task, {"user": user, "plan_entry_id": {"$in": [str(entry["_id"]) for entry in entries]}})
    quest_map = {quest["plan_entry_id"]: quest for quest in quests}
    result = []
    templates = await documents(PlanTemplate, {"user": user})
    template_map = {str(template["_id"]): template for template in templates}
    for entry in entries:
        item = public(entry)
        quest = quest_map.get(item["_id"])
        item["quest_id"] = str(quest["_id"]) if quest else None
        item["completed"] = quest.get("completed", False) if quest else item.get("completed", False)
        item["complete_date"] = quest.get("complete_date") if quest else item.get("complete_date")
        item["inactive"] = quest.get("inactive", False) if quest else False
        template = template_map.get(item.get("template_id"))
        item["repeating"] = bool(template and not template.get("ends_before"))
        result.append(item)
    goals = []
    for goal in (entry for entry in result if entry["kind"] == "goal" and not entry.get("cancelled")):
        parts = [entry for entry in result if entry["kind"] == "task" and entry.get("goal_id") == goal["_id"]]
        parts.sort(key=lambda entry: (entry["day"], entry.get("time") or "", entry["_id"]))
        goal["parts"] = parts
        goal["total"] = len(parts)
        goal["done"] = sum(part["completed"] and not part.get("cancelled") for part in parts)
        goal["completed"] = bool(parts) and goal["done"] == len(parts)
        goals.append(goal)
    boards = await documents(Board, {"username": user})
    boards.sort(key=lambda board: (board.get("order", 0), str(board["_id"])))
    return dict(
        week_start=week.isoformat(), week_end=(week + timedelta(days=6)).isoformat(),
        today=today(now).isoformat(), timezone="Europe/Moscow",
        entries=[entry for entry in result if entry["kind"] == "task"],
        goals=goals, boards=[public(board) for board in boards],
    )


async def create_entry(user, data, now=None):
    now = utc_datetime(now or datetime.now(timezone.utc))
    week = monday(data.day)
    if data.repeat and week < monday(today(now)):
        raise HTTPException(422, "Change future repetitions from the current or a future week")
    await prepare_week(user, week, now)
    board, goal = await validate_links(user, data, week.isoformat())
    content = {key: getattr(data, key) for key in CONTENT_FIELDS}
    template_id = None
    series_id = uuid4().hex
    day = week if data.kind == "goal" else data.day
    if data.repeat:
        template_id = ObjectId()
        series_id = str(template_id)
        template = PlanTemplate.model_validate(dict(
            _id=template_id, user=user, series_id=series_id, **content, weekday=day.weekday(), starts_on=day.isoformat(),
            goal_template_id=goal.get("template_id") if goal else None,
            created_at=now,
        )).model_dump(by_alias=True, exclude={"generated_through"})
        await collection(PlanTemplate).insert_one(template)
    entry = await upsert_occurrence(dict(
        user=user, **content, week_start=week.isoformat(), day=day.isoformat(),
        series_id=series_id, template_id=str(template_id) if template_id else None,
        goal_id=str(goal["_id"]) if goal else None,
        board_title=board["title"] if board else None, created_at=now,
    ))
    if data.kind == "task":
        await sync_quest(entry, now)
    await refresh(user, now)
    return public(entry)


async def update_entry(user, entry_id, data, now=None):
    now = utc_datetime(now or datetime.now(timezone.utc))
    await refresh(user, now)
    entry = await get_entry(user, entry_id)
    week = date.fromisoformat(entry["week_start"])
    if data.kind != entry["kind"] or monday(data.day) != week:
        raise HTTPException(422, "Keep the entry kind and choose a day from the same week")
    if (data.scope == "future" or (data.repeat and not entry.get("template_id"))) and week < monday(today(now)):
        raise HTTPException(422, "Change future repetitions from the current or a future week")
    if await entry_completed(entry):
        raise HTTPException(409, "Undo completion before editing the task")
    board, goal = await validate_links(user, data, week.isoformat())
    values = {key: getattr(data, key) for key in CONTENT_FIELDS}
    values.update(
        day=(week if data.kind == "goal" else data.day).isoformat(),
        goal_id=str(goal["_id"]) if goal else None,
        board_title=board["title"] if board else None,
    )
    if data.scope == "future" and entry.get("template_id"):
        template_values = {key: values[key] for key in CONTENT_FIELDS}
        template_values.update(weekday=data.day.weekday(), goal_template_id=goal.get("template_id") if goal else None)
        if not data.repeat:
            template_values["ends_before"] = entry["week_start"]
        else:
            template_values["ends_before"] = None
        await collection(PlanTemplate).update_one(
            {"_id": ObjectId(entry["template_id"]), "user": user}, {"$set": template_values},
        )
        following = await documents(PlanEntry, {"user": user, "series_id": entry["series_id"], "week_start": {"$gte": entry["week_start"]}})
        for target in following:
            if await entry_completed(target):
                continue
            target_values = dict(values)
            target_values["day"] = (date.fromisoformat(target["week_start"]) + timedelta(days=data.day.weekday() if data.kind == "task" else 0)).isoformat()
            if goal and target["week_start"] != entry["week_start"]:
                next_goal = await collection(PlanEntry).find_one({
                    "user": user, "template_id": goal.get("template_id"),
                    "week_start": target["week_start"], "cancelled": False,
                })
                target_values["goal_id"] = str(next_goal["_id"]) if next_goal else None
            if not data.repeat and target["week_start"] > entry["week_start"]:
                target_values = {
                    "cancelled": True,
                    "cancelled_by_series": target.get("cancelled_by_series", False) or not target.get("cancelled", False),
                }
            elif data.repeat and target.get("cancelled_by_series"):
                target_values.update(cancelled=False, cancelled_by_series=False)
            await collection(PlanEntry).update_one({"_id": target["_id"], "user": user}, {"$set": target_values})
            if target["kind"] == "task":
                await sync_quest({**target, **target_values}, now)
        if data.repeat:
            template = await collection(PlanTemplate).find_one({"_id": ObjectId(entry["template_id"]), "user": user})
            following_week = week
            while following_week <= monday(today(now)) + timedelta(weeks=HORIZON_WEEKS):
                await materialize_template(template, following_week, now)
                following_week += timedelta(weeks=1)
    else:
        # A single occurrence is a snapshot, so editing it never changes its template.
        if data.repeat and not entry.get("template_id"):
            template_id = ObjectId()
            template = PlanTemplate.model_validate(dict(
                _id=template_id, user=user, series_id=entry["series_id"],
                **{key: values[key] for key in CONTENT_FIELDS},
                weekday=data.day.weekday(), starts_on=values["day"], created_at=now,
                goal_template_id=goal.get("template_id") if goal else None,
            )).model_dump(by_alias=True, exclude={"generated_through"})
            await collection(PlanTemplate).insert_one(template)
            # Already-copied weeks are the same series: preserve their edits and avoid duplicates.
            await collection(PlanEntry).update_many(
                {"user": user, "series_id": entry["series_id"], "week_start": {"$gte": entry["week_start"]}},
                {"$set": {"template_id": str(template_id)}},
            )
            values.update(template_id=str(template_id))
        await collection(PlanEntry).update_one({"_id": entry["_id"], "user": user}, {"$set": values})
        if entry["kind"] == "task":
            await sync_quest({**entry, **values}, now)
        if data.repeat and not entry.get("template_id"):
            await refresh(user, now)
    return public(await get_entry(user, entry_id))


async def cancel_entry(user, entry_id, scope="single", now=None):
    await refresh(user, now)
    entry = await get_entry(user, entry_id)
    if scope == "future" and date.fromisoformat(entry["week_start"]) < monday(today(now)):
        raise HTTPException(422, "Change future repetitions from the current or a future week")
    if entry["kind"] == "task" and await entry_completed(entry):
        raise HTTPException(409, "Undo completion before deleting the task")
    query = {"_id": entry["_id"], "user": user}
    if scope == "future" and entry.get("template_id"):
        await collection(PlanTemplate).update_one(
            {"_id": ObjectId(entry["template_id"]), "user": user},
            {"$set": {"ends_before": entry["week_start"]}},
        )
        query = {"user": user, "series_id": entry["series_id"], "week_start": {"$gte": entry["week_start"]}}
    targets = await documents(PlanEntry, query)
    for target in targets:
        if target["kind"] == "task" and await entry_completed(target):
            continue
        await collection(PlanEntry).update_one({"_id": target["_id"]}, {"$set": {
            "cancelled": True, "cancelled_by_series": scope == "future" and bool(entry.get("template_id")),
        }})
        if target["kind"] == "goal":
            await collection(PlanEntry).update_many({"user": user, "goal_id": str(target["_id"])}, {"$set": {"goal_id": None}})
        else:
            await sync_quest({**target, "cancelled": True}, now)
    if entry["kind"] == "goal" and scope == "future" and entry.get("template_id"):
        await collection(PlanTemplate).update_many(
            {"user": user, "goal_template_id": entry["template_id"]}, {"$set": {"goal_template_id": None}},
        )


async def restore_entry(user, entry_id, now=None):
    entry = await get_entry(user, entry_id)
    await collection(PlanEntry).update_one({"_id": entry["_id"]}, {"$set": {"cancelled": False, "cancelled_by_series": False}})
    if entry["kind"] == "task":
        await sync_quest({**entry, "cancelled": False}, now)


async def set_completion(user, entry_id, completed, now=None):
    entry = await get_entry(user, entry_id)
    if entry["kind"] != "task" or entry.get("cancelled"):
        raise HTTPException(409, "This plan entry cannot be completed")
    now = utc_datetime(now or datetime.now(timezone.utc))
    if scheduled_datetime(datetime.fromisoformat(entry["day"])) > now:
        raise HTTPException(409, "Task is not active")
    if entry.get("board_id"):
        await sync_quest(entry, now)
        quest = await quest_for(entry)
        if quest is None:
            raise HTTPException(404, "Board not found")
        # Reuse the existing reward and undo rules; the plan reads this same quest.
        from tasks.requests import complete_task, uncomplete_task
        if quest.get("completed", False) == completed:
            return {"message": "Status unchanged"}
        return await (complete_task if completed else uncomplete_task)(ObjectId(quest["_id"]), user)
    await collection(PlanEntry).update_one(
        {"_id": entry["_id"], "user": user},
        {"$set": {"completed": completed, "complete_date": now if completed else None}},
    )
    return {"message": "Plan task updated"}


async def copy_next_week(user, day, now=None):
    week = monday(day)
    target_week = week + timedelta(weeks=1)
    await prepare_week(user, week, now)
    await prepare_week(user, target_week, now)
    source = await documents(PlanEntry, {"user": user, "week_start": week.isoformat(), "cancelled": False})
    source.sort(key=lambda entry: entry["kind"] != "goal")
    goal_ids = {}
    copied = 0
    for entry in source:
        existing = await collection(PlanEntry).find_one({"series_id": entry["series_id"], "week_start": target_week.isoformat()})
        fields = {key: entry.get(key) for key in (*CONTENT_FIELDS, "user", "series_id", "template_id", "board_title")}
        fields.update(
            week_start=target_week.isoformat(),
            day=(date.fromisoformat(entry["day"]) + timedelta(weeks=1)).isoformat(),
            goal_id=goal_ids.get(entry.get("goal_id")),
        )
        target = await upsert_occurrence(fields)
        if not existing:
            copied += 1
        if entry["kind"] == "goal" and not target.get("cancelled"):
            goal_ids[str(entry["_id"])] = str(target["_id"])
        if target["kind"] == "task":
            await sync_quest(target, now)
    return {"week_start": target_week.isoformat(), "copied": copied}
