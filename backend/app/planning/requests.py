"""Pure data transformations and validation for weekly planning."""

from datetime import datetime

from fastapi import HTTPException

from base.dates.calendar import start_of_week
from base.task_timing import scheduled_datetime, task_deadline


CONTENT_FIELDS = ("kind", "title", "description", "time", "end_time", "board_id")


def serialize_document(document):
    """Return a document copy with its MongoDB ID serialized as a string."""
    return {**document, "_id": str(document["_id"])}


def build_quest_fields(entry, board, now):
    """Build the quest's content, schedule and expiration state."""
    start = scheduled_datetime(datetime.fromisoformat(entry["day"]))
    deadline = task_deadline(start, board.get("task_expire_days"))
    return dict(
        title=entry["title"], description=entry.get("description", ""),
        board_id=entry["board_id"], date=start,
        inactive=deadline is not None and now >= deadline,
    )


def goals_first(records):
    """Order goals before tasks so parent entries exist before their parts."""
    return sorted(records, key=lambda record: record["kind"] != "goal")


def template_applies(template, day):
    """Check the inclusive start and exclusive end of a template's active dates."""
    return day >= template["starts_on"] and (
        not template.get("ends_before") or day < template["ends_before"]
    )


def build_plan_entry(entry, quest=None, template=None):
    """Prepare one entry with its quest status and repetition flag."""
    item = serialize_document(entry)
    status = quest if quest else entry
    item.update(
        quest_id=str(quest["_id"]) if quest else None,
        completed=status.get("completed", False),
        complete_date=status.get("complete_date"),
        inactive=quest.get("inactive", False) if quest else False,
        repeating=bool(template and not template.get("ends_before")),
    )
    return item


def build_week_goals(entries, tasks):
    """Attach sorted tasks and progress to each non-cancelled weekly goal."""
    goals = []
    for entry in entries:
        if entry["kind"] != "goal" or entry.get("cancelled"):
            continue
        parts = [task for task in tasks if task.get("goal_id") == entry["_id"]]
        parts.sort(key=lambda task: (task["day"], task.get("time") or "", task["_id"]))
        done = sum(part["completed"] and not part.get("cancelled") for part in parts)
        goals.append({
            **entry,
            "parts": parts,
            "total": len(parts),
            "done": done,
            "completed": bool(parts) and done == len(parts),
        })
    return goals


def build_entry_values(data, board, goal):
    """Build shared entry content and links, placing weekly goals on Monday."""
    day = start_of_week(data.day) if data.kind == "goal" else data.day
    return dict(
        **{key: getattr(data, key) for key in CONTENT_FIELDS},
        day=day.isoformat(),
        goal_id=str(goal["_id"]) if goal else None,
        board_title=board["title"] if board else None,
    )


def validate_completion(entry, now):
    """Allow completion changes only for non-cancelled tasks whose scheduled day has begun."""
    if entry["kind"] != "task" or entry.get("cancelled"):
        raise HTTPException(409, "This plan entry cannot be completed")
    if scheduled_datetime(datetime.fromisoformat(entry["day"])) > now:
        raise HTTPException(409, "Task is not active")
