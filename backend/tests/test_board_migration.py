import pytest

from migrations import boards as migration
from models.models import Board, User


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
        assert board["award_points"] == board["award_xp"] == migration.baseBoards_points[category]
        assert board["task_expire_days"] == expiry
        assert board["is_weekly"] is (category == "hard")
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
    assert board["is_weekly"] is True


@pytest.mark.asyncio
async def test_existing_hard_board_missing_weekly_setting_is_backfilled(database):
    db, _ = database
    board_id = db.boards.insert_one({
        "username": "alice", "title": "Трудные", "order": 2,
        "award_points": 200, "award_xp": 200, "task_expire_days": 7,
    }).inserted_id
    db.tasks.insert_one({"user": "alice", "board_id": str(board_id), "completed": False})

    await migration.migrate_tasks_to_boards()

    assert db.boards.find_one({"_id": board_id})["is_weekly"] is True
    before = snapshot(db)
    await migration.migrate_tasks_to_boards()
    assert snapshot(db) == before


@pytest.mark.asyncio
async def test_other_boards_keep_weekly_settings_and_default_to_false(database):
    db, _ = database
    db.boards.insert_many([
        {"username": "alice", "title": "Простые"},
        {"username": "alice", "title": "Обычные", "is_weekly": False},
        {"username": "alice", "title": "Своя недельная", "is_weekly": True},
    ])

    await migration.migrate_tasks_to_boards()

    assert db.boards.find_one({"title": "Простые"})["is_weekly"] is False
    assert db.boards.find_one({"title": "Обычные"})["is_weekly"] is False
    assert db.boards.find_one({"title": "Своя недельная"})["is_weekly"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("is_weekly", [False, True])
async def test_existing_hard_board_preserves_explicit_weekly_setting(database, is_weekly):
    db, _ = database
    board_id = db.boards.insert_one({
        "username": "alice", "title": "Трудные", "is_weekly": is_weekly,
        "award_points": 3, "award_xp": 4, "task_expire_days": None,
    }).inserted_id
    db.tasks.insert_one({"user": "alice", "type": "hard", "completed": False})

    await migration.migrate_tasks_to_boards()
    await migration.migrate_tasks_to_boards()

    board = db.boards.find_one({"_id": board_id})
    assert board["is_weekly"] is is_weekly
    assert (board["award_points"], board["award_xp"]) == (3, 4)
    assert board["task_expire_days"] is None
    assert db.boards.count_documents({}) == 1


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


@pytest.mark.asyncio
async def test_obsolete_board_flag_is_removed_before_loading_documents(database):
    db, _ = database
    board_id = db.boards.insert_one({
        "username": "alice", "title": "Простые", "is_custom": True,
        "task_expire_days": None, "award_points": 3, "award_xp": 4,
    }).inserted_id

    await migration.migrate_tasks_to_boards()

    stored = db.boards.find_one({"_id": board_id})
    assert "is_custom" not in stored
    assert stored["task_expire_days"] is None
    assert (stored["award_points"], stored["award_xp"]) == (3, 4)
    Board.model_validate(stored)
    before = snapshot(db)
    await migration.migrate_tasks_to_boards()
    assert snapshot(db) == before
