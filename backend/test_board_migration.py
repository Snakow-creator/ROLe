import sys
from pathlib import Path

import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).parent / "app"))

from migrations import boards as migration
from models.models import Board, Task, User


class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.cursor)
        except StopIteration:
            raise StopAsyncIteration

    async def to_list(self, length=None):
        return list(self.cursor)


class Collection:
    def __init__(self, collection):
        self.raw = collection
        self.fail_cleanup_once = False

    def find(self, query):
        return Cursor(self.raw.find(query))

    async def aggregate(self, pipeline):
        return Cursor(self.raw.aggregate(pipeline))

    async def update_many(self, query, update):
        return self.raw.update_many(query, update)

    async def update_one(self, query, update):
        if self.fail_cleanup_once and "$unset" in update:
            self.fail_cleanup_once = False
            raise RuntimeError("Simulated interruption before user cleanup")
        return self.raw.update_one(query, update)

    async def count_documents(self, query):
        return self.raw.count_documents(query)


class Field:
    def __init__(self, name):
        self.name = name

    def __eq__(self, value):
        return {self.name: value}


@pytest.fixture
def database(monkeypatch):
    db = mongomock.MongoClient().role_migration_test
    collections = {name: Collection(db[name]) for name in ("boards", "tasks", "users")}
    for model, name in [(Board, "boards"), (Task, "tasks"), (User, "users")]:
        collection = collections[name]
        monkeypatch.setattr(model, "get_pymongo_collection", classmethod(lambda cls, c=collection: c))
    monkeypatch.setattr(Board, "username", Field("username"), raising=False)
    monkeypatch.setattr(Board, "title", Field("title"), raising=False)

    async def find_one(cls, *conditions):
        document = db.boards.find_one({"$and": list(conditions)})
        return cls.model_validate(document) if document else None

    async def insert(self):
        document = self.model_dump(by_alias=True)
        document.pop("_id", None)
        self.id = db.boards.insert_one(document).inserted_id
        return self

    monkeypatch.setattr(Board, "find_one", classmethod(find_one))
    monkeypatch.setattr(Board, "insert", insert)
    return db, collections


def snapshot(db):
    return {name: list(db[name].find()) for name in ("boards", "tasks", "users")}


@pytest.mark.asyncio
async def test_old_database_transfers_all_user_categories_without_losing_history(database):
    db, _ = database
    counts = dict(zip(migration.OLD_DEFAULT_BOARDS, [7, 3, 2, 1, 0]))
    db.users.insert_one({
        "name": "alice", "hashed_password": "hash",
        **{f"complete_{category}_tasks": count for category, count in counts.items()},
    })
    # The user counter retains completions whose task documents were deleted.
    db.tasks.insert_one({"user": "alice", "type": "simple", "completed": True})
    db.tasks.insert_one({"user": "alice", "type": "simple", "completed": False})

    await migration.migrate_tasks_to_boards()
    assert db.boards.count_documents({"username": "alice"}) == 5
    for category, count in counts.items():
        title, _, expiry = migration.OLD_DEFAULT_BOARDS[category]
        board = db.boards.find_one({"username": "alice", "title": title})
        assert board["completed_tasks"] == count
        assert board["award_points"] == board["award_xp"] == migration.baseTasks_points[category]
        assert board["task_expire_days"] == expiry
    assert db.tasks.count_documents({"type": {"$exists": True}}) == 0
    migrated_user = db.users.find_one({"name": "alice"})
    assert not any(field.startswith("complete_") for field in migrated_user)
    User.model_validate(migrated_user)
    before = snapshot(db)
    await migration.migrate_tasks_to_boards()
    assert snapshot(db) == before


@pytest.mark.asyncio
async def test_previous_board_migration_keeps_user_history_and_existing_rewards(database):
    db, _ = database
    board_id = db.boards.insert_one({
        "username": "alice", "title": "Простые", "order": 0,
        "award_points": 83, "award_xp": 29,
    }).inserted_id
    db.users.insert_one({"name": "alice", "complete_simple_tasks": 12})
    db.tasks.insert_one({"user": "alice", "board_id": str(board_id), "completed": True})
    await migration.migrate_tasks_to_boards()
    board = db.boards.find_one({"_id": board_id})
    assert board["completed_tasks"] == 12
    assert (board["award_points"], board["award_xp"]) == (83, 29)
    assert db.boards.count_documents({}) == 1
    assert "complete_simple_tasks" not in db.users.find_one({"name": "alice"})


@pytest.mark.asyncio
async def test_missing_user_history_is_rebuilt_from_completed_board_tasks(database):
    db, _ = database
    custom_id = db.boards.insert_one({"username": "alice", "title": "Своя доска"}).inserted_id
    empty_id = db.boards.insert_one({"username": "alice", "title": "Пустая доска"}).inserted_id
    db.tasks.insert_many([
        {"user": "alice", "board_id": str(custom_id), "completed": True},
        {"user": "alice", "board_id": str(custom_id), "completed": True, "inactive": True},
        {"user": "alice", "board_id": str(custom_id), "completed": False},
        {"user": "bob", "board_id": str(custom_id), "completed": True},
    ])
    await migration.migrate_tasks_to_boards()
    assert db.boards.find_one({"_id": custom_id})["completed_tasks"] == 2
    assert db.boards.find_one({"_id": empty_id})["completed_tasks"] == 0
    before = snapshot(db)
    await migration.migrate_tasks_to_boards()
    assert snapshot(db) == before


@pytest.mark.asyncio
async def test_old_tasks_without_user_counters_are_counted_after_conversion(database):
    db, _ = database
    db.tasks.insert_many([
        {"user": "alice", "type": "hard", "completed": True},
        {"user": "alice", "type": "hard", "completed": False},
    ])
    await migration.migrate_tasks_to_boards()
    board = db.boards.find_one({"username": "alice", "title": "Трудные"})
    assert board["completed_tasks"] == 1


@pytest.mark.asyncio
async def test_existing_higher_counter_and_other_users_are_preserved(database):
    db, _ = database
    board_id = db.boards.insert_one({
        "username": "alice", "title": "Простые", "completed_tasks": 15,
    }).inserted_id
    db.users.insert_many([
        {"name": "alice", "complete_simple_tasks": 7},
        {"name": "bob", "complete_simple_tasks": 3},
    ])
    await migration.migrate_tasks_to_boards()
    assert db.boards.find_one({"_id": board_id})["completed_tasks"] == 15
    assert db.boards.find_one({"username": "bob", "title": "Простые"})["completed_tasks"] == 3


@pytest.mark.asyncio
async def test_retry_after_interruption_does_not_double_count(database):
    db, collections = database
    db.users.insert_one({"name": "alice", "complete_simple_tasks": 9})
    collections["users"].fail_cleanup_once = True
    with pytest.raises(RuntimeError):
        await migration.migrate_tasks_to_boards()
    assert db.users.find_one({"name": "alice"})["complete_simple_tasks"] == 9
    assert db.boards.find_one({"username": "alice", "title": "Простые"})["completed_tasks"] == 9
    await migration.migrate_tasks_to_boards()
    assert "complete_simple_tasks" not in db.users.find_one({"name": "alice"})
    assert db.boards.find_one({"username": "alice", "title": "Простые"})["completed_tasks"] == 9


@pytest.mark.asyncio
async def test_invalid_old_counter_is_not_deleted(database):
    db, _ = database
    db.users.insert_one({"name": "alice", "complete_simple_tasks": -1})
    with pytest.raises(ValueError):
        await migration.migrate_tasks_to_boards()
    assert db.users.find_one({"name": "alice"})["complete_simple_tasks"] == -1
