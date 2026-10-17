import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from base.task_timing import (
    TASK_TIMEZONE, expired_date_filter, scheduled_datetime, task_deadline,
)
from models.models import Task
from models.schemas import TaskSchema
from repositories import task_repo
from tasks import requests as task_requests, scheduler, task_service
from test_gameplay import Document, quest, setup_quest, user


def local(day, hour=0, minute=0, second=0):
    return datetime(2026, 10, day, hour, minute, second, tzinfo=TASK_TIMEZONE)


@pytest.mark.parametrize("task_date", [
    local(12), local(12, 23, 59),
    datetime(2026, 10, 12),  # Existing naive UTC dates from MongoDB.
])
def test_daily_deadline_is_next_calendar_day_at_noon(task_date):
    assert task_deadline(task_date, 1) == local(13, 12)


@pytest.mark.parametrize("start,expected", [
    (datetime(2026, 10, 31, 23, tzinfo=TASK_TIMEZONE), datetime(2026, 11, 1, 12, tzinfo=TASK_TIMEZONE)),
    (datetime(2026, 12, 31, tzinfo=TASK_TIMEZONE), datetime(2027, 1, 1, 12, tzinfo=TASK_TIMEZONE)),
])
def test_daily_deadline_crosses_month_and_year_boundaries(start, expected):
    assert task_deadline(start, 1) == expected


@pytest.mark.parametrize("days", [0, 2, 7, 30, None])
def test_other_board_deadlines_keep_their_duration(days):
    start = local(12, 18)
    expected = None if days is None else start + timedelta(days=days)
    assert task_deadline(start, days) == expected


@pytest.mark.parametrize("now", [local(13), local(13, 11, 59, 59), local(13, 12), local(14)])
@pytest.mark.parametrize("days", [0, 1, 7, 30])
@pytest.mark.parametrize("start", [local(11), local(12), local(12, 23, 59), local(13), local(14)])
def test_batch_cutoff_and_completion_deadline_agree(now, days, start):
    operator, cutoff = next(iter(expired_date_filter(days, now).items()))
    selected = start < cutoff if operator == "$lt" else start <= cutoff
    assert selected == (task_deadline(start, days) <= now)


def test_date_only_tasks_start_at_moscow_midnight():
    assert scheduled_datetime(datetime(2026, 10, 13)) == datetime(
        2026, 10, 12, 21, tzinfo=timezone.utc
    )
    assert scheduled_datetime(local(13, 18)) == local(13, 18)


def test_missing_date_uses_today_instead_of_an_invisible_null_date(monkeypatch):
    from base import task_timing

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return local(13, 1).astimezone(tz)

    monkeypatch.setattr(task_timing, "datetime", Clock)
    assert scheduled_datetime(None) == local(13)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload_date,expected_start", [
    (None, local(12, 23, 59, 17)),
    ("2026-10-14", local(14)),
    ("2026-10-14T18:30:00+03:00", local(14, 18, 30)),
])
async def test_creation_saves_exact_server_time_and_preserves_schedule(
    database, monkeypatch, payload_date, expected_start,
):
    from repositories import task_repository

    db, _ = database
    now = local(12, 23, 59, 17)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    async def insert(self):
        document = self.model_dump(by_alias=True)
        document.pop("_id", None)
        self.id = db.tasks.insert_one(document).inserted_id
        return self

    monkeypatch.setattr(task_repository, "datetime", Clock)
    monkeypatch.setattr(Task, "insert", insert)
    payload = dict(title="Late task", description="", board_id="daily")
    if payload_date is not None:
        payload["date"] = payload_date
    # The client cannot replace the server's creation timestamp.
    payload["created_at"] = "2000-01-01T00:00:00Z"
    task = await task_repo.insert_task(TaskSchema(**payload), "alice")
    stored = db.tasks.find_one({"_id": task.id})
    assert stored["created_at"] == now.astimezone(timezone.utc).replace(tzinfo=None)
    assert stored["date"] == expected_start.astimezone(timezone.utc).replace(tzinfo=None)


def test_legacy_task_keeps_unknown_creation_time(database):
    task = Task.model_validate(dict(
        title="Old task", description="", board_id="daily", user="alice", date=local(12),
    ))
    assert task.created_at is None
    assert task.date == local(12)


@pytest.mark.asyncio
async def test_refresh_expires_only_due_unfinished_tasks_and_is_repeatable(database, monkeypatch):
    db, _ = database
    records = [
        {"title": "yesterday", "board_id": "daily", "date": local(12)},
        {"title": "today", "board_id": "daily", "date": local(13)},
        {"title": "future", "board_id": "daily", "date": local(14)},
        {"title": "completed", "board_id": "daily", "date": local(11), "completed": True},
        {"title": "expired", "board_id": "daily", "date": local(11), "inactive": True},
        {"title": "no deadline", "board_id": "unlimited", "date": local(1)},
        {"title": "weekly", "board_id": "weekly", "date": local(12)},
        {"title": "weekly due", "board_id": "weekly", "date": local(1)},
    ]
    for record in records:
        db.tasks.insert_one({"completed": False, "inactive": False, **record})

    groups = [{"_id": 1, "board_id": ["daily"]}, {"_id": 7, "board_id": ["weekly"]}]
    get_boards = AsyncMock(return_value=groups)
    monkeypatch.setattr("tasks.service.board_repo.get_expire_boards", get_boards)

    class UpdateQuery:
        def __init__(self, query):
            self.query = query

        async def update(self, changes):
            db.tasks.update_many(self.query, changes)

    monkeypatch.setattr(Task, "find", classmethod(lambda cls, query: UpdateQuery(query)))

    await task_service.update("alice", now=local(13, 11, 59))
    assert not db.tasks.find_one({"title": "yesterday"})["inactive"]
    assert db.tasks.find_one({"title": "weekly due"})["inactive"]
    await task_service.update("alice", now=local(13, 12))
    assert db.tasks.find_one({"title": "yesterday"})["inactive"]
    for title in ["today", "future", "completed", "no deadline", "weekly"]:
        assert not db.tasks.find_one({"title": title})["inactive"]
    before = list(db.tasks.find())
    await task_service.update("alice", now=local(13, 12))
    assert list(db.tasks.find()) == before
    get_boards.assert_called_with("alice")


@pytest.mark.asyncio
@pytest.mark.parametrize("now,expired", [(local(13, 11, 59, 59), False), (local(13, 12), True)])
async def test_completion_checks_noon_without_waiting_for_scheduler(monkeypatch, now, expired):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    monkeypatch.setattr(task_requests, "datetime", Clock)
    player = user(last_streak=now)
    task = quest(date=local(12))
    board = Document(
        username="alice", title="Daily", award_points=20, award_xp=10,
        is_weekly=False, task_expire_days=1,
    )
    setup_quest(monkeypatch, player, task, board)
    if expired:
        with pytest.raises(HTTPException) as error:
            await task_requests.complete_task(task.id, player.name)
        assert error.value.status_code == 409
        assert task.inactive
        assert player.Spoints == player.xp == board.completed_tasks == 0
    else:
        await task_requests.complete_task(task.id, player.name)
        assert task.completed
        assert player.Spoints > 0


@pytest.mark.asyncio
async def test_scheduler_retries_after_failure_and_stops_on_shutdown(monkeypatch, caplog):
    succeeded = asyncio.Event()
    update = AsyncMock(side_effect=[RuntimeError("temporary database outage"), None])

    async def tick():
        await update()
        succeeded.set()

    monkeypatch.setattr(scheduler.task_service, "update", tick)
    async with scheduler.task_update_scheduler(interval=0.001) as worker:
        await asyncio.wait_for(succeeded.wait(), timeout=1)
        assert not worker.done()
    assert worker.cancelled()
    assert update.await_count == 2
    assert "Scheduled task update failed" in caplog.text


@pytest.mark.asyncio
async def test_lifespan_catches_up_starts_scheduler_and_closes_database_last(monkeypatch):
    import main as application

    events = []

    class Client:
        def __getitem__(self, name):
            return "database"

        async def close(self):
            events.append("database closed")

    async def update():
        events.append("tasks updated")

    @asynccontextmanager
    async def scheduled_updates():
        events.append("scheduler started")
        try:
            yield
        finally:
            events.append("scheduler stopped")

    monkeypatch.setattr(application, "AsyncMongoClient", lambda url: Client())
    monkeypatch.setattr(application.beanie, "init_beanie", AsyncMock())
    monkeypatch.setattr(application, "migrate_tasks_to_boards", AsyncMock())
    monkeypatch.setattr(application.task_service, "update", update)
    monkeypatch.setattr(application, "users_days_and_last_mul_expired", AsyncMock())
    monkeypatch.setattr(application, "load_security_handle_errors", lambda app: None)
    monkeypatch.setattr(application, "load_data", AsyncMock())
    monkeypatch.setattr(application, "task_update_scheduler", scheduled_updates)

    async with application.main(SimpleNamespace()):
        assert events == ["tasks updated", "scheduler started"]
    assert events == ["tasks updated", "scheduler started", "scheduler stopped", "database closed"]
