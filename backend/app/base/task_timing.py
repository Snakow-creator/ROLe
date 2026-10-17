"""Shared task deadlines for background updates and completion requests."""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


TASK_TIMEZONE = ZoneInfo("Europe/Moscow")
DAILY_DEADLINE = time(12)


def utc_datetime(value: datetime) -> datetime:
    # PyMongo returns naive UTC datetimes unless tz_aware is enabled.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def scheduled_datetime(value: datetime | None) -> datetime:
    """Date-only input is local midnight; explicit offsets keep their instant."""
    if value is None:
        value = datetime.now(TASK_TIMEZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif value.tzinfo is None:
        value = value.replace(tzinfo=TASK_TIMEZONE)
    return value.astimezone(timezone.utc)


def task_deadline(task_date: datetime, days: int | None) -> datetime | None:
    if days is None:
        return None
    task_date = utc_datetime(task_date)
    if days == 1:
        next_day = task_date.astimezone(TASK_TIMEZONE).date() + timedelta(days=1)
        return datetime.combine(next_day, DAILY_DEADLINE, TASK_TIMEZONE).astimezone(timezone.utc)
    return task_date + timedelta(days=days)


def expired_date_filter(days: int, now: datetime) -> dict:
    """Select precisely the task dates whose deadline has already passed."""
    now = utc_datetime(now)
    if days == 1:
        local_now = now.astimezone(TASK_TIMEZONE)
        cutoff_day = local_now.date()
        if local_now.time() < DAILY_DEADLINE:
            cutoff_day -= timedelta(days=1)
        cutoff = datetime.combine(cutoff_day, time.min, TASK_TIMEZONE)
        return {"$lt": cutoff.astimezone(timezone.utc)}
    return {"$lte": now - timedelta(days=days)}
