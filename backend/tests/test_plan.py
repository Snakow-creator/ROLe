from datetime import date, datetime
from unittest.mock import AsyncMock

import pytest
from beanie import PydanticObjectId as ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api.core.security import security
from base.task_timing import TASK_TIMEZONE
from planning import handler, planning_service
from planning.schemas import PlanEntryInput
from models.models import Task
from boards import board_service
from tasks import handler as quest_handler, task_service as quest_service


NOW = datetime(2026, 10, 12, 14, tzinfo=TASK_TIMEZONE)
WEEK = date(2026, 10, 12)
NEXT_WEEK = date(2026, 10, 19)


@pytest.fixture
def plan_db(database):
    db, _ = database
    db.plan_entries.create_index([("series_id", 1), ("week_start", 1)], unique=True)
    db.plan_templates.create_index("series_id", unique=True, partialFilterExpression={"series_id": {"$type": "string"}})
    db.tasks.create_index("plan_entry_id", unique=True, partialFilterExpression={"plan_entry_id": {"$type": "string"}})
    return db


def data(**changes):
    return PlanEntryInput(**{"title": "Read", "day": WEEK, **changes})


async def week(user="alice", day=WEEK, now=NOW):
    return await planning_service.get_weekly_plan(user, day, now)


def add_board(db, user="alice"):
    return str(db.boards.insert_one(dict(
        username=user, title="Study", order=0, award_points=20, award_xp=10,
        task_expire_days=1, is_weekly=False,
    )).inserted_id)


@pytest.mark.asyncio
async def test_repeating_tasks_are_independent_snapshots_with_finite_horizon(plan_db):
    entry = await planning_service.create_entry("alice", data(time="18:00", end_time="19:00"), NOW)
    assert plan_db.plan_templates.count_documents({}) == 1
    assert plan_db.plan_entries.count_documents({}) == 3
    await planning_service.set_completion("alice", entry["_id"], True, NOW)
    current = await week()
    following = await week(day=NEXT_WEEK)
    assert current["entries"][0]["completed"]
    assert not following["entries"][0]["completed"]
    assert current["entries"][0]["_id"] != following["entries"][0]["_id"]
    assert following["entries"][0]["time"] == "18:00"
    await planning_service.refresh("alice", NOW)
    assert plan_db.plan_entries.count_documents({}) == 3


@pytest.mark.asyncio
async def test_one_off_tasks_do_not_repeat_until_explicitly_copied(plan_db):
    entry = await planning_service.create_entry("alice", data(repeat=False), NOW)
    await planning_service.set_completion("alice", entry["_id"], True, NOW)
    assert not (await week(day=NEXT_WEEK))["entries"]
    result = await planning_service.copy_next_week("alice", WEEK, NOW)
    assert result["copied"] == 1
    assert not (await week(day=NEXT_WEEK))["entries"][0]["completed"]
    assert (await week())["entries"][0]["completed"]
    assert (await planning_service.copy_next_week("alice", WEEK, NOW))["copied"] == 0
    assert plan_db.plan_entries.count_documents({}) == 2


@pytest.mark.asyncio
async def test_copy_preserves_existing_next_week_edits_and_independent_tasks(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    next_entry = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.update_entry("alice", next_entry["_id"], data(title="Changed", day=NEXT_WEEK), NOW)
    await planning_service.create_entry("alice", data(title="One-off", day=NEXT_WEEK, repeat=False), NOW)
    await planning_service.copy_next_week("alice", WEEK, NOW)
    assert {entry["title"] for entry in (await week(day=NEXT_WEEK))["entries"]} == {"Changed", "One-off"}


@pytest.mark.asyncio
async def test_single_edit_does_not_change_template_or_other_weeks(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    next_entry = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.update_entry("alice", next_entry["_id"], data(title="Only Tuesday", day=date(2026, 10, 20)), NOW)
    assert (await week())["entries"][0]["title"] == "Read"
    assert (await week(day=NEXT_WEEK))["entries"][0]["day"] == "2026-10-20"
    assert (await week(day=date(2026, 10, 26)))["entries"][0]["title"] == "Read"
    assert plan_db.plan_templates.find_one({})["title"] == "Read"


@pytest.mark.asyncio
async def test_future_edit_preserves_history_and_updates_prepared_distant_weeks(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    await week(day=date(2026, 12, 7))
    next_entry = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.update_entry("alice", next_entry["_id"], data(title="New series", day=date(2026, 10, 20), scope="future"), NOW)
    assert (await week())["entries"][0]["title"] == "Read"
    assert (await week(day=date(2026, 12, 7)))["entries"][0]["title"] == "New series"
    assert (await week(day=NEXT_WEEK))["entries"][0]["day"] == "2026-10-20"


@pytest.mark.asyncio
async def test_goal_parts_repeat_into_the_matching_goal_and_reset_progress(plan_db):
    goal = await planning_service.create_entry("alice", data(kind="goal", title="Portfolio"), NOW)
    first = await planning_service.create_entry("alice", data(goal_id=goal["_id"]), NOW)
    await planning_service.create_entry("alice", data(title="Write", day=date(2026, 10, 14), goal_id=goal["_id"]), NOW)
    await planning_service.set_completion("alice", first["_id"], True, NOW)
    current = await week()
    following = await week(day=NEXT_WEEK)
    assert (current["goals"][0]["done"], current["goals"][0]["total"]) == (1, 2)
    assert (following["goals"][0]["done"], following["goals"][0]["total"]) == (0, 2)
    assert all(entry["goal_id"] == following["goals"][0]["_id"] for entry in following["entries"])
    await planning_service.set_completion("alice", first["_id"], False, NOW)
    assert (await week())["goals"][0]["done"] == 0


@pytest.mark.asyncio
async def test_cancelled_goal_part_keeps_its_segment_and_can_be_restored(plan_db):
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    part = await planning_service.create_entry("alice", data(goal_id=goal["_id"]), NOW)
    await planning_service.cancel_entry("alice", part["_id"], now=NOW)
    current = await week()
    assert current["goals"][0]["total"] == 1
    assert current["goals"][0]["parts"][0]["cancelled"]
    assert not current["goals"][0]["completed"]
    await planning_service.restore_entry("alice", part["_id"], NOW)
    assert not (await week())["entries"][0]["cancelled"]


@pytest.mark.asyncio
async def test_goal_deletion_keeps_its_daily_tasks(plan_db):
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    await planning_service.create_entry("alice", data(goal_id=goal["_id"]), NOW)
    await planning_service.cancel_entry("alice", goal["_id"], now=NOW)
    current = await week()
    assert not current["goals"]
    assert current["entries"][0]["goal_id"] is None
    assert not current["entries"][0]["cancelled"]
    assert (await week(day=NEXT_WEEK))["goals"]


@pytest.mark.asyncio
async def test_linked_quest_is_unique_and_hidden_until_assigned_day(plan_db):
    board_id = add_board(plan_db)
    entry = await planning_service.create_entry("alice", data(board_id=board_id), NOW)
    assert plan_db.tasks.count_documents({}) == 3
    await planning_service.refresh("alice", NOW)
    await week()
    assert plan_db.tasks.count_documents({}) == 3
    quest = plan_db.tasks.find_one({"plan_entry_id": entry["_id"]})
    assert quest["board_id"] == board_id
    assert quest["date"] == datetime(2026, 10, 11, 21)
    future = plan_db.tasks.find_one({"date": {"$gt": NOW.replace(tzinfo=None)}})
    assert future and future["completed"] is False


@pytest.mark.asyncio
async def test_completion_reuses_quest_rewards_and_reads_quest_status_both_ways(plan_db, monkeypatch):
    board_id = add_board(plan_db)
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    entry = await planning_service.create_entry("alice", data(board_id=board_id, goal_id=goal["_id"]), NOW)

    async def complete(quest_id, user):
        plan_db.tasks.update_one({"_id": quest_id, "user": user}, {"$set": {"completed": True}})
        return {"points": 20, "message": "completed"}

    complete_mock = AsyncMock(side_effect=complete)
    monkeypatch.setattr(quest_service, "complete_task", complete_mock)
    result = await planning_service.set_completion("alice", entry["_id"], True, NOW)
    assert result["points"] == 20
    assert (await week())["goals"][0]["done"] == 1
    await planning_service.set_completion("alice", entry["_id"], True, NOW)
    complete_mock.assert_awaited_once()
    # An undo from the quests view is immediately reflected by the same source of truth.
    plan_db.tasks.update_one({"plan_entry_id": entry["_id"]}, {"$set": {"completed": False}})
    assert (await week())["goals"][0]["done"] == 0


@pytest.mark.asyncio
async def test_deleting_board_preserves_plan_history_and_stops_future_quest_generation(plan_db):
    board_id = add_board(plan_db)
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    entry = await planning_service.create_entry("alice", data(board_id=board_id, goal_id=goal["_id"]), NOW)
    plan_db.tasks.update_one({"plan_entry_id": entry["_id"]}, {"$set": {"completed": True}})
    await board_service.delete_board(board_id, "alice")
    await planning_service.refresh("alice", NOW)
    current = await week()
    assert current["entries"][0]["board_id"] is None
    assert current["entries"][0]["completed"]
    assert current["goals"][0]["done"] == 1
    assert plan_db.tasks.count_documents({}) == 0
    assert plan_db.plan_templates.count_documents({"board_id": board_id}) == 0


@pytest.mark.asyncio
async def test_board_deletion_retry_keeps_plan_history_after_quests_are_removed(plan_db, monkeypatch):
    board_id = add_board(plan_db)
    entry = await planning_service.create_entry("alice", data(board_id=board_id), NOW)
    plan_db.tasks.update_one({"plan_entry_id": entry["_id"]}, {"$set": {"completed": True}})
    boards = board_service.board_repo.model.get_pymongo_collection()
    delete_one = boards.delete_one
    monkeypatch.setattr(boards, "delete_one", AsyncMock(side_effect=RuntimeError("board deletion failed")))

    with pytest.raises(RuntimeError, match="board deletion failed"):
        await board_service.delete_board(board_id, "alice")
    assert plan_db.tasks.count_documents({"board_id": board_id}) == 0
    assert plan_db.boards.find_one({"_id": ObjectId(board_id)}) is not None

    monkeypatch.setattr(boards, "delete_one", delete_one)
    result = await board_service.delete_board(board_id, "alice")
    assert result["deleted_tasks"] == 0
    preserved = (await week())["entries"][0]
    assert preserved["completed"]
    assert preserved["board_id"] is None


@pytest.mark.asyncio
async def test_cancellation_survives_refresh_and_future_cancellation_keeps_history(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    next_entry = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.cancel_entry("alice", next_entry["_id"], scope="future", now=NOW)
    await planning_service.refresh("alice", NOW)
    assert not (await week())["entries"][0]["cancelled"]
    assert (await week(day=NEXT_WEEK))["entries"][0]["cancelled"]
    assert not (await week(day=date(2026, 12, 7)))["entries"]


@pytest.mark.asyncio
async def test_copy_one_off_goals_and_parts_keeps_relationships(plan_db):
    goal = await planning_service.create_entry("alice", data(kind="goal", repeat=False), NOW)
    await planning_service.create_entry("alice", data(goal_id=goal["_id"], repeat=False), NOW)
    assert (await planning_service.copy_next_week("alice", WEEK, NOW))["copied"] == 2
    following = await week(day=NEXT_WEEK)
    assert following["entries"][0]["goal_id"] == following["goals"][0]["_id"]
    assert following["goals"][0]["total"] == 1


@pytest.mark.asyncio
async def test_copy_distant_week_does_not_generate_intervening_weeks(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    result = await planning_service.copy_next_week("alice", date(2026, 12, 7), NOW)
    assert result == {"week_start": "2026-12-14", "copied": 0}
    assert set(plan_db.plan_entries.distinct("week_start")) == {
        "2026-10-12", "2026-10-19", "2026-10-26", "2026-12-07", "2026-12-14",
    }


@pytest.mark.asyncio
async def test_future_cancellation_preserves_completed_occurrences(plan_db):
    entry = await planning_service.create_entry("alice", data(), NOW)
    following = (await week(day=NEXT_WEEK))["entries"][0]
    plan_db.plan_entries.update_one(
        {"_id": ObjectId(following["_id"])}, {"$set": {"completed": True}},
    )
    await planning_service.cancel_entry("alice", entry["_id"], scope="future", now=NOW)
    preserved = (await week(day=NEXT_WEEK))["entries"][0]
    assert preserved["completed"] and not preserved["cancelled"]
    assert (await week(day=date(2026, 10, 26)))["entries"][0]["cancelled"]


@pytest.mark.asyncio
async def test_future_goal_cancellation_detaches_tasks_without_stopping_their_repetitions(plan_db):
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    await planning_service.create_entry("alice", data(goal_id=goal["_id"]), NOW)
    await planning_service.cancel_entry("alice", goal["_id"], scope="future", now=NOW)
    future = await week(day=date(2026, 12, 7))
    assert not future["goals"]
    assert len(future["entries"]) == 1
    assert future["entries"][0]["goal_id"] is None
    assert future["entries"][0]["repeating"]
    assert not future["entries"][0]["cancelled"]


@pytest.mark.asyncio
@pytest.mark.parametrize("completed", [False, True])
async def test_removing_board_keeps_only_completed_linked_quests(plan_db, completed):
    entry = await planning_service.create_entry("alice", data(board_id=add_board(plan_db), repeat=False), NOW)
    plan_db.tasks.update_one({"plan_entry_id": entry["_id"]}, {"$set": {"completed": completed}})
    await planning_service.sync_quest({**entry, "board_id": None}, NOW)
    assert plan_db.tasks.count_documents({"plan_entry_id": entry["_id"]}) == int(completed)


@pytest.mark.asyncio
async def test_refresh_catches_up_after_downtime_without_duplicate_occurrences(plan_db):
    await planning_service.create_entry("alice", data(), NOW)
    later = datetime(2026, 11, 16, 14, tzinfo=TASK_TIMEZONE)
    await planning_service.refresh("alice", later)
    assert plan_db.plan_entries.count_documents({}) == 8
    await planning_service.refresh("alice", later)
    assert plan_db.plan_entries.count_documents({}) == 8


@pytest.mark.asyncio
async def test_future_tasks_cannot_be_completed_early(plan_db):
    entry = await planning_service.create_entry("alice", data(day=NEXT_WEEK, repeat=False), NOW)
    with pytest.raises(HTTPException) as error:
        await planning_service.set_completion("alice", entry["_id"], True, NOW)
    assert error.value.status_code == 409
    assert not (await week(day=NEXT_WEEK))["entries"][0]["completed"]


@pytest.mark.asyncio
async def test_repetition_can_be_stopped_and_reenabled_without_restoring_single_cancellations(plan_db):
    original = await planning_service.create_entry("alice", data(), NOW)
    following = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.cancel_entry("alice", following["_id"], now=NOW)
    await planning_service.update_entry("alice", original["_id"], data(scope="future", repeat=False), NOW)
    assert not (await week())["entries"][0]["repeating"]
    await planning_service.update_entry("alice", original["_id"], data(scope="future", repeat=True), NOW)
    assert (await week())["entries"][0]["repeating"]
    assert (await week(day=NEXT_WEEK))["entries"][0]["cancelled"]
    assert not (await week(day=date(2026, 10, 26)))["entries"][0]["cancelled"]


@pytest.mark.asyncio
async def test_enabling_repetition_on_a_copied_one_off_does_not_duplicate_next_week(plan_db):
    original = await planning_service.create_entry("alice", data(repeat=False), NOW)
    await planning_service.copy_next_week("alice", WEEK, NOW)
    following = (await week(day=NEXT_WEEK))["entries"][0]
    await planning_service.update_entry("alice", following["_id"], data(title="Keep this edit", day=NEXT_WEEK, repeat=False), NOW)
    await planning_service.update_entry("alice", original["_id"], data(repeat=True), NOW)
    next_entries = (await week(day=NEXT_WEEK))["entries"]
    assert len(next_entries) == 1
    assert next_entries[0]["title"] == "Keep this edit"
    assert next_entries[0]["repeating"]


@pytest.mark.asyncio
async def test_deleting_completed_quest_keeps_rewards_and_cannot_be_regenerated(plan_db, monkeypatch):
    board_id = add_board(plan_db)
    goal = await planning_service.create_entry("alice", data(kind="goal"), NOW)
    entry = await planning_service.create_entry("alice", data(board_id=board_id, goal_id=goal["_id"]), NOW)
    plan_db.tasks.update_one({"plan_entry_id": entry["_id"]}, {"$set": {
        "completed": True, "awarded_points": 30, "awarded_xp": 15,
    }})
    record = plan_db.tasks.find_one({"plan_entry_id": entry["_id"]})
    quest = Task.model_validate(record)

    async def update(self, changes):
        plan_db.tasks.update_one({"_id": self.id}, changes)

    monkeypatch.setattr(Task, "update", update)
    monkeypatch.setattr(quest_handler.task_service.task_repo, "get", AsyncMock(return_value=quest))
    await quest_handler.edit_delete_task(quest.id, {"name": "alice"})
    await planning_service.refresh("alice", NOW)
    assert plan_db.tasks.count_documents({"plan_entry_id": entry["_id"]}) == 1
    assert (await week())["goals"][0]["done"] == 0
    await planning_service.restore_entry("alice", entry["_id"], NOW)
    restored = plan_db.tasks.find_one({"_id": quest.id})
    assert restored["completed"]
    assert (restored["awarded_points"], restored["awarded_xp"]) == (30, 15)
    assert (await week())["goals"][0]["done"] == 1


@pytest.mark.asyncio
async def test_completed_tasks_must_be_undone_before_edit_or_delete(plan_db):
    entry = await planning_service.create_entry("alice", data(repeat=False), NOW)
    await planning_service.set_completion("alice", entry["_id"], True, NOW)
    for action in [
        planning_service.update_entry("alice", entry["_id"], data(repeat=False), NOW),
        planning_service.cancel_entry("alice", entry["_id"], now=NOW),
    ]:
        with pytest.raises(HTTPException) as error:
            await action
        assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_foreign_board_and_goal_cannot_be_linked(plan_db):
    board_id = add_board(plan_db, "bob")
    with pytest.raises(HTTPException) as error:
        await planning_service.create_entry("alice", data(board_id=board_id), NOW)
    assert error.value.status_code == 404
    foreign_goal = await planning_service.create_entry("bob", data(kind="goal"), NOW)
    with pytest.raises(HTTPException) as error:
        await planning_service.create_entry("alice", data(goal_id=foreign_goal["_id"]), NOW)
    assert error.value.status_code == 404
    assert not (await week())["entries"]


def make_client(authenticated=True):
    app = FastAPI()
    app.include_router(handler.router)
    security.handle_errors(app)
    if authenticated:
        for route in app.routes:
            if not hasattr(route, "dependant"):
                continue
            for dependency in route.dependant.dependencies:
                app.dependency_overrides[dependency.call] = (
                    (lambda: {"name": "alice"}) if dependency.name == "user" else (lambda: None)
                )
    return TestClient(app)


def test_api_requires_authentication(plan_db):
    with make_client(authenticated=False) as client:
        assert client.get("/plan").status_code == 401
        assert client.post("/plan/entries", json={"title": "Task", "day": "2026-10-12"}).status_code == 401


@pytest.mark.parametrize("changes", [
    {"title": " "}, {"title": "x" * 101}, {"description": "x" * 256},
    {"day": "not-a-date"}, {"time": "25:30"}, {"time": "9:00"},
    {"time": "18:00", "end_time": "17:00"}, {"end_time": "18:00"},
    {"board_id": "bad"}, {"goal_id": "bad"}, {"user": "bob"},
    {"completed": True}, {"kind": "board"}, {"scope": "all"},
    {"repeat": "true"},
    {"kind": "goal", "time": "18:00"},
])
def test_api_validates_fields_before_writing(plan_db, changes):
    with make_client() as client:
        response = client.post("/plan/entries", json={"title": "Task", "day": "2026-10-12", **changes})
    assert response.status_code == 422
    assert plan_db.plan_entries.count_documents({}) == 0


def test_foreign_entries_cannot_be_changed_or_completed(plan_db, monkeypatch):
    entry_id = plan_db.plan_entries.insert_one(dict(user="bob", title="Private", kind="task")).inserted_id
    monkeypatch.setattr(handler.task_service, "update", AsyncMock())
    with make_client() as client:
        for method, path, payload in [
            (client.put, f"/plan/entries/{entry_id}", {"title": "Hack", "day": "2026-10-12"}),
            (client.put, f"/plan/entries/{entry_id}/completion", {"completed": True}),
            (client.delete, f"/plan/entries/{entry_id}", None),
            (client.post, f"/plan/entries/{entry_id}/restore", None),
        ]:
            response = method(path, json=payload) if payload is not None else method(path)
            assert response.status_code == 404
    assert plan_db.plan_entries.find_one({"_id": entry_id})["title"] == "Private"
