from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId as ObjectId
from fastapi import HTTPException

from base.dates.calendar import start_of_week, today
from base.task_timing import utc_datetime
from models.models import PlanTemplate, Task
from planning import requests as plan_requests
import tasks


class PlanningService:
    """Coordinate weekly planning through a supplied planning repository."""

    HORIZON_WEEKS = 2  # Current week and the next two weeks.

    def __init__(self, repository, task_repo, board_repo):
        """Store the repository used by all planning operations."""
        self.repository = repository
        self.task_repo = task_repo
        self.board_repo = board_repo

    async def get_entry(self, user, entry_id):
        """Find a user-owned plan entry or report an invalid or missing ID."""
        if not ObjectId.is_valid(entry_id):
            raise HTTPException(422, "Invalid plan entry ID")
        entry = await self.repository.get_entry(user, entry_id)
        if entry is None:
            raise HTTPException(404, "Plan entry not found")
        return entry

    async def quest_for(self, entry):
        """Find the quest linked to a plan entry."""
        return await self.task_repo.get_quest(entry["user"], entry["_id"])

    async def entry_completed(self, entry):
        """Read completion from the linked quest when available, otherwise from the entry."""
        quest = await self.quest_for(entry) if entry.get("board_id") else None
        return quest.get("completed", False) if quest else entry.get("completed", False)

    async def _validate_goal_link(self, user, data, week):
        """Resolve an optional goal and validate its week and repetition rules."""
        if not data.goal_id:
            return None
        goal = await self.get_entry(user, data.goal_id)
        if goal["kind"] != "goal" or goal["week_start"] != week or goal.get("cancelled"):
            raise HTTPException(422, "Choose an active goal from the same week")
        if data.repeat and not goal.get("template_id"):
            raise HTTPException(422, "A repeating task requires a repeating goal")
        return goal

    async def validate_links(self, user, data, week):
        """Resolve and validate the entry's optional board and parent goal."""
        board = await self.board_repo.get_owned_board(data.board_id, user) if data.board_id else None
        if data.board_id and board is None:
            raise HTTPException(404, "Board not found")
        goal = await self._validate_goal_link(user, data, week)
        return board, goal

    async def _save_linked_quest(self, entry, fields, now):
        """Create the linked quest or update its fields while it is unfinished."""
        if await self.quest_for(entry):
            await self.task_repo.update_uncompleted_quest(entry["user"], entry["_id"], fields)
            return
        quest = Task.model_validate(dict(
            _id=ObjectId(), user=entry["user"], plan_entry_id=str(entry["_id"]),
            created_at=now, **fields,
        )).model_dump(by_alias=True)
        await self.task_repo.insert_quest_if_missing(quest)

    async def sync_quest(self, entry, now=None):
        """Synchronize the linked quest with the entry's board and cancellation state."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        if entry.get("cancelled"):
            await self.task_repo.deactivate_quests(entry["user"], entry["_id"])
        elif not entry.get("board_id"):
            await self.task_repo.delete_uncompleted_quests(entry["user"], entry["_id"])
        else:
            board = await self.board_repo.get_owned_board(entry["board_id"], entry["user"])
            if board is not None:
                await self._save_linked_quest(entry, plan_requests.build_quest_fields(entry, board, now), now)

    async def _template_links(self, template, week):
        """Resolve the board and the parent goal occurrence for the requested week."""
        goal = None
        if template.get("goal_template_id"):
            goal = await self.repository.get_active_template_entry(
                template["user"], template["goal_template_id"], week.isoformat(),
            )
        board = None
        if template.get("board_id"):
            board = await self.board_repo.get_owned_board(template["board_id"], template["user"])
        return board, goal

    async def materialize_template(self, template, week, now=None):
        """Ensure an applicable template has an occurrence and linked quest for one week."""
        day = week + timedelta(days=template["weekday"] if template["kind"] == "task" else 0)
        if not plan_requests.template_applies(template, day.isoformat()):
            return
        board, goal = await self._template_links(template, week)
        entry = await self.repository.upsert_occurrence(dict(
            **{key: template.get(key) for key in plan_requests.CONTENT_FIELDS},
            user=template["user"], week_start=week.isoformat(), day=day.isoformat(),
            template_id=str(template["_id"]), series_id=template.get("series_id") or str(template["_id"]),
            goal_id=str(goal["_id"]) if goal else None,
            board_title=board["title"] if board else None,
        ))
        if entry["kind"] == "task":
            await self.sync_quest(entry, now)

    async def _catch_up_template(self, template, horizon, now):
        """Generate missing weeks and advance the template cursor after each successful week."""
        week = start_of_week(date.fromisoformat(template["starts_on"]))
        if template.get("generated_through"):
            week = max(week, date.fromisoformat(template["generated_through"]) + timedelta(weeks=1))
        while week <= horizon:
            await self.materialize_template(template, week, now)
            await self.repository.advance_template_cursor(template["_id"], week.isoformat())
            week += timedelta(weeks=1)

    async def _refresh_templates(self, user, horizon, now):
        """Catch up applicable templates, generating goals before their tasks."""
        templates = await self.repository.get_templates(
            user, starts_by=(horizon + timedelta(days=6)).isoformat(),
        )
        for template in plan_requests.goals_first(templates):
            await self._catch_up_template(template, horizon, now)

    async def _repair_recent_quests(self, user, horizon, now):
        """Repair linked quests without regenerating historical plan entries."""
        from_week = start_of_week(today(now)) - timedelta(weeks=1)
        entries = await self.repository.get_entries_to_repair(
            user, from_week.isoformat(), horizon.isoformat(),
        )
        for entry in entries:
            await self.sync_quest(entry, now)

    async def refresh(self, user=None, now=None):
        """Bring repeating entries and recent linked quests up to date."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        horizon = start_of_week(today(now)) + timedelta(weeks=self.HORIZON_WEEKS)
        await self._refresh_templates(user, horizon, now)
        await self._repair_recent_quests(user, horizon, now)

    async def _prepare_future_week(self, user, week, now):
        """Generate a requested distant week without generating intervening weeks."""
        horizon = start_of_week(today(now)) + timedelta(weeks=self.HORIZON_WEEKS)
        if week <= horizon:
            return
        templates = await self.repository.get_templates(user)
        for template in plan_requests.goals_first(templates):
            await self.materialize_template(template, week, now)

    async def _prepare_weeks(self, user, weeks, now):
        """Refresh once, then prepare any requested weeks beyond the normal horizon."""
        await self.refresh(user, now)
        for week in weeks:
            await self._prepare_future_week(user, week, now)

    async def prepare_week(self, user, week, now=None):
        """Ensure the requested week is ready for reading or editing."""
        await self._prepare_weeks(user, [week], now)

    async def _load_week_entries(self, user, week):
        """Load weekly entries and attach their quest and template data."""
        entries = await self.repository.get_week_entries(user, week.isoformat())
        quests = await self.task_repo.get_quests(user, [str(entry["_id"]) for entry in entries])
        templates = await self.repository.get_templates(user)
        quest_map = {quest["plan_entry_id"]: quest for quest in quests}
        template_map = {str(template["_id"]): template for template in templates}
        return [
            plan_requests.build_plan_entry(
                entry,
                quest_map.get(str(entry["_id"])),
                template_map.get(entry.get("template_id")),
            )
            for entry in entries
        ]

    async def _load_plan_boards(self, user):
        """Return the user's boards in display order with string IDs."""
        boards = await self.board_repo.get_board_documents(user)
        boards.sort(key=lambda board: (board.get("order", 0), str(board["_id"])))
        return [plan_requests.serialize_document(board) for board in boards]

    async def get_weekly_plan(self, user, day=None, now=None):
        """Prepare a week and assemble its tasks, goals and boards for the API."""
        week = start_of_week(day or today(now))
        await self.prepare_week(user, week, now)
        entries = await self._load_week_entries(user, week)
        tasks = [entry for entry in entries if entry["kind"] == "task"]
        goals = plan_requests.build_week_goals(entries, tasks)
        boards = await self._load_plan_boards(user)
        return dict(
            week_start=week.isoformat(),
            week_end=(week + timedelta(days=6)).isoformat(),
            today=today(now).isoformat(),
            timezone="Europe/Moscow",
            entries=tasks,
            goals=goals,
            boards=boards,
        )

    async def _create_entry_template(self, user, data, day, goal, now, *, series_id=None, weekday=None):
        """Save a repeat template, preserving an existing series ID when supplied."""
        template_id = ObjectId()
        template = PlanTemplate.model_validate(dict(
            _id=template_id, user=user, series_id=series_id or str(template_id),
            **{key: getattr(data, key) for key in plan_requests.CONTENT_FIELDS},
            weekday=day.weekday() if weekday is None else weekday, starts_on=day.isoformat(),
            goal_template_id=goal.get("template_id") if goal else None,
            created_at=now,
        )).model_dump(by_alias=True, exclude={"generated_through"})
        await self.repository.insert_template(template)
        return str(template_id)

    async def create_entry(self, user, data, now=None):
        """Create a plan entry, its optional repeat template and its linked quest."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        week = start_of_week(data.day)
        if data.repeat and week < start_of_week(today(now)):
            raise HTTPException(422, "Change future repetitions from the current or a future week")
        await self.prepare_week(user, week, now)
        board, goal = await self.validate_links(user, data, week.isoformat())
        values = plan_requests.build_entry_values(data, board, goal)
        day = date.fromisoformat(values["day"])
        template_id = await self._create_entry_template(user, data, day, goal, now) if data.repeat else None
        entry = await self.repository.upsert_occurrence(dict(
            user=user, **values, week_start=week.isoformat(), created_at=now,
            # Copies share a series ID even when the entry has no repeat template.
            series_id=template_id or str(ObjectId()), template_id=template_id,
        ))
        if data.kind == "task":
            await self.sync_quest(entry, now)
        await self.refresh(user, now)
        return plan_requests.serialize_document(entry)

    async def _validate_entry_update(self, entry, data, now):
        """Reject changes to the entry kind, week, completed state or past repetitions."""
        week = date.fromisoformat(entry["week_start"])
        if data.kind != entry["kind"] or start_of_week(data.day) != week:
            raise HTTPException(422, "Keep the entry kind and choose a day from the same week")
        changes_repetitions = data.scope == "future" or (data.repeat and not entry.get("template_id"))
        if changes_repetitions and week < start_of_week(today(now)):
            raise HTTPException(422, "Change future repetitions from the current or a future week")
        if await self.entry_completed(entry):
            raise HTTPException(409, "Undo completion before editing the task")

    async def _save_entry_changes(self, user, entry, values, now):
        """Save entry fields and synchronize its linked quest when it is a task."""
        await self.repository.update_entry(user, entry["_id"], values)
        if entry["kind"] == "task":
            await self.sync_quest({**entry, **values}, now)

    async def _series_occurrence_values(self, source, target, data, values, goal):
        """Adapt series changes to one week, preserving individual cancellations."""
        target_values = dict(values)
        weekday = data.day.weekday() if data.kind == "task" else 0
        target_values["day"] = (date.fromisoformat(target["week_start"]) + timedelta(days=weekday)).isoformat()
        if goal and target["week_start"] != source["week_start"]:
            next_goal = await self.repository.get_active_template_entry(
                target["user"], goal.get("template_id"), target["week_start"],
            )
            target_values["goal_id"] = str(next_goal["_id"]) if next_goal else None
        if not data.repeat and target["week_start"] > source["week_start"]:
            return {
                "cancelled": True,
                "cancelled_by_series": target.get("cancelled_by_series", False) or not target.get("cancelled", False),
            }
        if data.repeat and target.get("cancelled_by_series"):
            target_values.update(cancelled=False, cancelled_by_series=False)
        return target_values

    async def _update_series_template(self, user, entry, data, values, goal):
        """Save content, parent goal and repetition settings for future occurrences."""
        template_values = {key: values[key] for key in plan_requests.CONTENT_FIELDS}
        template_values.update(
            weekday=data.day.weekday(),
            goal_template_id=goal.get("template_id") if goal else None,
            ends_before=None if data.repeat else entry["week_start"],
        )
        await self.repository.update_template(user, entry["template_id"], template_values)

    async def _update_series_occurrences(self, user, entry, data, values, goal, now):
        """Apply a series edit to existing occurrences while preserving completed ones."""
        following = await self.repository.get_series_entries(user, entry["series_id"], entry["week_start"])
        for target in following:
            if await self.entry_completed(target):
                continue
            target_values = await self._series_occurrence_values(entry, target, data, values, goal)
            await self._save_entry_changes(user, target, target_values, now)

    async def _materialize_series(self, user, entry, now):
        """Fill missing weeks of an edited series without advancing its generation cursor."""
        template = await self.repository.get_template(user, entry["template_id"])
        week = date.fromisoformat(entry["week_start"])
        horizon = start_of_week(today(now)) + timedelta(weeks=self.HORIZON_WEEKS)
        while week <= horizon:
            await self.materialize_template(template, week, now)
            week += timedelta(weeks=1)

    async def _update_entry_series(self, user, entry, data, values, goal, now):
        """Update a series template and its current and future unfinished occurrences."""
        await self._update_series_template(user, entry, data, values, goal)
        await self._update_series_occurrences(user, entry, data, values, goal, now)
        if data.repeat:
            await self._materialize_series(user, entry, now)

    async def _enable_entry_repetition(self, user, entry, data, values, goal, now):
        """Create a template and link existing copies without replacing their contents."""
        template_id = await self._create_entry_template(
            user, data, date.fromisoformat(values["day"]), goal, now,
            series_id=entry["series_id"], weekday=data.day.weekday(),
        )
        await self.repository.link_series_template(
            user, entry["series_id"], entry["week_start"], template_id,
        )
        return {**values, "template_id": template_id}

    async def _update_single_entry(self, user, entry, data, values, goal, now):
        """Edit one occurrence, optionally enabling repetition for its existing series."""
        enable_repetition = data.repeat and not entry.get("template_id")
        if enable_repetition:
            values = await self._enable_entry_repetition(user, entry, data, values, goal, now)
        await self._save_entry_changes(user, entry, values, now)
        if enable_repetition:
            await self.refresh(user, now)

    async def update_entry(self, user, entry_id, data, now=None):
        """Validate an edit and apply it to one occurrence or the remaining series."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        await self.refresh(user, now)
        entry = await self.get_entry(user, entry_id)
        await self._validate_entry_update(entry, data, now)
        board, goal = await self.validate_links(user, data, entry["week_start"])
        values = plan_requests.build_entry_values(data, board, goal)
        if data.scope == "future" and entry.get("template_id"):
            await self._update_entry_series(user, entry, data, values, goal, now)
        else:
            await self._update_single_entry(user, entry, data, values, goal, now)
        return plan_requests.serialize_document(await self.get_entry(user, entry_id))

    async def _validate_cancellation(self, entry, scope, now):
        """Reject cancellation of completed tasks or future repetitions from a past week."""
        if scope == "future" and date.fromisoformat(entry["week_start"]) < start_of_week(today(now)):
            raise HTTPException(422, "Change future repetitions from the current or a future week")
        if entry["kind"] == "task" and await self.entry_completed(entry):
            raise HTTPException(409, "Undo completion before deleting the task")

    async def _cancellation_targets(self, user, entry, cancel_series):
        """Select one entry or all occurrences of its series from the selected week onward."""
        if not cancel_series:
            return [entry]
        return await self.repository.get_series_entries(user, entry["series_id"], entry["week_start"])

    async def _cancel_occurrence(self, user, entry, cancel_series, now):
        """Cancel an unfinished occurrence and update its linked quest or detach its parts."""
        if entry["kind"] == "task" and await self.entry_completed(entry):
            return
        await self._save_entry_changes(user, entry, {
            "cancelled": True, "cancelled_by_series": cancel_series,
        }, now)
        if entry["kind"] == "goal":
            await self.repository.detach_goal_parts(user, str(entry["_id"]))

    async def cancel_entry(self, user, entry_id, scope="single", now=None):
        """Cancel a plan entry or its future repetitions while preserving completed tasks."""
        await self.refresh(user, now)
        entry = await self.get_entry(user, entry_id)
        await self._validate_cancellation(entry, scope, now)
        cancel_series = scope == "future" and bool(entry.get("template_id"))
        if cancel_series:
            await self.repository.update_template(user, entry["template_id"], {"ends_before": entry["week_start"]})
        targets = await self._cancellation_targets(user, entry, cancel_series)
        for target in targets:
            await self._cancel_occurrence(user, target, cancel_series, now)
        if entry["kind"] == "goal" and cancel_series:
            await self.repository.detach_goal_templates(user, entry["template_id"])

    async def restore_entry(self, user, entry_id, now=None):
        """Restore one cancelled occurrence and synchronize its linked quest."""
        entry = await self.get_entry(user, entry_id)
        await self._save_entry_changes(user, entry, {"cancelled": False, "cancelled_by_series": False}, now)

    async def _set_quest_completion(self, user, entry, completed, now):
        """Delegate completion to the quest's existing reward and undo rules."""
        await self.sync_quest(entry, now)
        quest = await self.quest_for(entry)
        if quest is None:
            raise HTTPException(404, "Board not found")
        if quest.get("completed", False) == completed:
            return {"message": "Status unchanged"}
        action = tasks.task_service.complete_task if completed else tasks.task_service.uncomplete_task
        return await action(ObjectId(quest["_id"]), user)

    async def _set_plan_completion(self, user, entry, completed, now):
        """Save completion directly for a plan task without a linked board."""
        await self.repository.update_entry(user, entry["_id"], {
            "completed": completed, "complete_date": now if completed else None,
        })
        return {"message": "Plan task updated"}

    async def set_completion(self, user, entry_id, completed, now=None):
        """Validate a completion change and route it to the plan or linked quest."""
        entry = await self.get_entry(user, entry_id)
        now = utc_datetime(now or datetime.now(timezone.utc))
        plan_requests.validate_completion(entry, now)
        if entry.get("board_id"):
            return await self._set_quest_completion(user, entry, completed, now)
        return await self._set_plan_completion(user, entry, completed, now)

    async def _copy_occurrence(self, entry, target_week, goal_ids):
        """Copy one occurrence to the next week without replacing an existing series entry."""
        existing = await self.repository.get_occurrence(entry["series_id"], target_week.isoformat())
        fields = {key: entry.get(key) for key in (*plan_requests.CONTENT_FIELDS, "user", "series_id", "template_id", "board_title")}
        fields.update(
            week_start=target_week.isoformat(),
            day=(date.fromisoformat(entry["day"]) + timedelta(weeks=1)).isoformat(),
            goal_id=goal_ids.get(entry.get("goal_id")),
        )
        target = await self.repository.upsert_occurrence(fields)
        return target, existing is None

    async def _copy_week_entries(self, user, week, target_week, now):
        """Copy goals before tasks, remapping parent goal IDs and counting new entries."""
        source = await self.repository.get_week_entries(user, week.isoformat(), active_only=True)
        goal_ids = {}
        copied = 0
        for entry in plan_requests.goals_first(source):
            target, created = await self._copy_occurrence(entry, target_week, goal_ids)
            copied += created
            if entry["kind"] == "goal" and not target.get("cancelled"):
                goal_ids[str(entry["_id"])] = str(target["_id"])
            if target["kind"] == "task":
                await self.sync_quest(target, now)
        return copied

    async def copy_next_week(self, user, day, now=None):
        """Prepare both weeks once and copy missing entries into the next week."""
        week = start_of_week(day)
        target_week = week + timedelta(weeks=1)
        await self._prepare_weeks(user, [week, target_week], now)
        copied = await self._copy_week_entries(user, week, target_week, now)
        return {"week_start": target_week.isoformat(), "copied": copied}
