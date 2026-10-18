from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.core.security import security
from boards import handler as board_handlers
from migrations import boards as migration
from models.models import Board
from tasks import handler as task_handlers


@pytest.fixture
def board_database(database, monkeypatch):
    db, _ = database

    class BoardCursor:
        def __init__(self, query):
            self.query = query

        async def to_list(self):
            return [Board.model_validate(document) for document in db.boards.find(self.query)]

    def find(cls, *conditions):
        return BoardCursor({"$and": list(conditions)})

    monkeypatch.setattr(Board, "find", classmethod(find))
    return db


def make_client(authenticated=True):
    app = FastAPI()
    app.include_router(board_handlers.router)
    app.include_router(task_handlers.router)
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


def test_create_board_saves_settings_and_returns_it_on_reload(board_database, monkeypatch):
    db = board_database
    db.boards.insert_many([
        {"username": "alice", "title": "Первая", "order": 0},
        {"username": "alice", "title": "Последняя", "order": 1},
        {"username": "bob", "title": "Чужая", "order": 99},
    ])
    monkeypatch.setattr(task_handlers.task_service, "update", AsyncMock())
    monkeypatch.setattr(task_handlers.task_service.task_repo, "get_user_tasks", AsyncMock(return_value=[]))

    with make_client() as client:
        response = client.post("/add/board", json={
            "title": "  Учёба  ", "award_points": 25, "award_xp": 10,
            "is_weekly": True, "task_expire_days": 7,
        })
        assert response.status_code == 201
        board = response.json()["board"]
        assert board["_id"]
        assert board["username"] == "alice"
        assert board["title"] == "Учёба"
        assert board["order"] == 2
        assert (board["award_points"], board["award_xp"]) == (25, 10)
        assert board["is_weekly"] is True
        assert board["task_expire_days"] == 7
        assert board["completed_tasks"] == 0

        stored = db.boards.find_one({"title": "Учёба"})
        assert "is_custom" not in stored
        reloaded = client.get("/tasks").json()["boards"]
        assert [entry["order"] for entry in reloaded] == [0, 1, 2]
        assert reloaded[-1]["_id"] == board["_id"]
        assert not any(entry["username"] == "bob" for entry in reloaded)


def test_first_board_has_zero_order_and_no_expiration(board_database):
    with make_client() as client:
        response = client.post("/add/board", json={"title": "Первая"})
    assert response.status_code == 201
    board = response.json()["board"]
    assert board["order"] == 0
    assert board["task_expire_days"] is None
    assert board["award_points"] == board["award_xp"] == 0
    assert board["is_weekly"] is False


@pytest.mark.parametrize("changes", [
    {"title": ""}, {"title": "   "}, {"title": "я" * 101},
    {"award_points": -1}, {"award_points": 1.5}, {"award_points": True},
    {"award_xp": -1}, {"award_xp": 1.5},
    {"is_weekly": "false"},
    {"task_expire_days": 0}, {"task_expire_days": -1},
    {"task_expire_days": 0.5}, {"task_expire_days": 36501},
    {"username": "bob"}, {"order": -1}, {"completed_tasks": 99},
    {"is_custom": False},
])
def test_invalid_or_server_owned_fields_do_not_create_board(board_database, changes):
    with make_client() as client:
        response = client.post("/add/board", json={"title": "Доска", **changes})
    assert response.status_code == 422
    assert board_database.boards.count_documents({}) == 0


def test_unauthenticated_creation_does_not_save_board(board_database):
    with make_client(authenticated=False) as client:
        response = client.post("/add/board", json={"title": "Доска"})
    assert response.status_code == 401
    assert board_database.boards.count_documents({}) == 0


@pytest.mark.asyncio
async def test_custom_default_title_keeps_user_settings_during_migration(board_database):
    db = board_database
    with make_client() as client:
        response = client.post("/add/board", json={
            "title": "Простые", "award_points": 3, "award_xp": 4,
            "is_weekly": True, "task_expire_days": None,
        })
    assert response.status_code == 201
    board_id = db.boards.find_one({"username": "alice", "title": "Простые"})["_id"]
    db.tasks.insert_one({"user": "alice", "type": "simple", "completed": False})

    await migration.migrate_tasks_to_boards()
    await migration.migrate_tasks_to_boards()

    board = db.boards.find_one({"_id": board_id})
    assert board["task_expire_days"] is None
    assert (board["award_points"], board["award_xp"]) == (3, 4)
    assert board["is_weekly"] is True
    assert db.boards.count_documents({}) == 1
    assert db.tasks.find_one({})["board_id"] == str(board_id)
