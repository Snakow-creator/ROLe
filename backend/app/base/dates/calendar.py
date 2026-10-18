"""Week boundaries and current dates in the application's timezone."""

from datetime import date, datetime, timedelta, timezone

from base.task_timing import TASK_TIMEZONE, utc_datetime


def start_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def today(now: datetime | None = None) -> date:
    return utc_datetime(now or datetime.now(timezone.utc)).astimezone(TASK_TIMEZONE).date()


def as_utc_datetime(value: datetime | str) -> datetime:
    """Normalize stored ISO strings and naive or aware datetimes to UTC."""
    return utc_datetime(datetime.fromisoformat(value) if isinstance(value, str) else value)
