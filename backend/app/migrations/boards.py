# migrations/boards.py
import logging

from boards.data import baseBoards_points
from models.models import Board, Task, User

logger = logging.getLogger(__name__)

# type -> (title, order, expire_days)
OLD_DEFAULT_BOARDS = {
    "simple": ("Простые", 0, 1),
    "common": ("Обычные", 1, 1),
    "hard": ("Трудные", 2, 7),
    "expert": ("Сложные", 3, 30),
    "hardcore": ("Хардкорные", 4, None),
}
DEFAULT_BOARD = ("Прочее", 5, None)


async def _remove_obsolete_board_fields():
    boards_col = Board.get_pymongo_collection()
    await boards_col.update_many(
        {"is_custom": {"$exists": True}},
        {"$unset": {"is_custom": ""}},
    )


async def _backfill_board_expiration():
    boards_col = Board.get_pymongo_collection()
    for title, _, expire_days in OLD_DEFAULT_BOARDS.values():
        if expire_days is None:
            continue
        # Only repair missing fields. An explicit None means no expiration,
        # including user-created boards with a legacy category's title.
        await boards_col.update_many(
            {"title": title, "task_expire_days": {"$exists": False}},
            {"$set": {"task_expire_days": expire_days}},
        )


async def _backfill_board_weekly():
    boards_col = Board.get_pymongo_collection()
    hard_title = OLD_DEFAULT_BOARDS["hard"][0]
    # Restore the legacy weekly bonus without overwriting explicit settings.
    await boards_col.update_many(
        {"title": hard_title, "is_weekly": {"$exists": False}},
        {"$set": {"is_weekly": True}},
    )
    await boards_col.update_many(
        {"is_weekly": {"$exists": False}},
        {"$set": {"is_weekly": False}},
    )


async def _backfill_board_awards():
    boards_col = Board.get_pymongo_collection()
    updated = 0

    # Restore the old rewards without overwriting configured board rewards.
    for old_type, (title, _, _) in OLD_DEFAULT_BOARDS.items():
        award = baseBoards_points[old_type]
        for field in ("award_points", "award_xp"):
            result = await boards_col.update_many(
                {"title": title, field: {"$exists": False}},
                {"$set": {field: award}},
            )
            updated += result.modified_count

    # Other boards have no legacy reward; use the Board model defaults.
    for field in ("award_points", "award_xp"):
        result = await boards_col.update_many(
            {field: {"$exists": False}},
            {"$set": {field: 0}},
        )
        updated += result.modified_count

    logger.info("Added %d missing board reward fields", updated)


async def _get_or_create_board(
    username: str,
    title: str,
    order: int,
    expire_days: int | None = None,
    award_points: int = 0,
    award_xp: int = 0,
    is_weekly: bool = False,
):
    board = await Board.find_one(
        Board.username == username,
        Board.title == title,
    )
    if not board:
        board = Board(
            username=username,
            title=title,
            order=order,
            task_expire_days=expire_days,
            award_points=award_points,
            award_xp=award_xp,
            is_weekly=is_weekly,
        )
        await board.insert()
        logger.info("Created board '%s' for user %s", title, username)
    return board


async def _migrate_user_completed_tasks():
    users_col = User.get_pymongo_collection()
    boards_col = Board.get_pymongo_collection()
    legacy_fields = {
        old_type: f"complete_{old_type}_tasks"
        for old_type in OLD_DEFAULT_BOARDS
    }
    query = {"$or": [{field: {"$exists": True}} for field in legacy_fields.values()]}

    # Read raw documents: the new User model no longer accepts these fields.
    async for user in users_col.find(query):
        for old_type, field in legacy_fields.items():
            if field not in user:
                continue
            count = user[field]
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError(f"Invalid legacy completed-task counter: {field}")
            title, order, expire_days = OLD_DEFAULT_BOARDS[old_type]
            award = baseBoards_points[old_type]
            board = await _get_or_create_board(
                user["name"], title, order, expire_days,
                award_points=award, award_xp=award,
                is_weekly=old_type == "hard",
            )
            # A retry after interruption must not add the same history twice.
            # Preserve a board counter if it already contains a larger total.
            await boards_col.update_one(
                {"_id": board.id},
                {"$max": {"completed_tasks": count}},
            )

        # Delete legacy fields only after all of this user's counters are saved.
        await users_col.update_one(
            {"_id": user["_id"]},
            {"$unset": {field: "" for field in legacy_fields.values()}},
        )


async def _backfill_board_completed_tasks():
    boards_col = Board.get_pymongo_collection()
    tasks_col = Task.get_pymongo_collection()

    # Also handles databases already migrated from type to board_id, including
    # custom boards and users whose legacy counters have already been removed.
    async for board in boards_col.find({}):
        count = await tasks_col.count_documents({
            "board_id": str(board["_id"]),
            "user": board["username"],
            "completed": True,
        })
        await boards_col.update_one(
            {"_id": board["_id"]},
            {"$max": {"completed_tasks": count}},
        )


async def migrate_tasks_to_boards():
    # Remove the obsolete field before loading documents with extra="forbid".
    await _remove_obsolete_board_fields()
    # Run even when every task already has board_id and no old type remains.
    await _backfill_board_awards()
    await _backfill_board_expiration()
    await _backfill_board_weekly()
    tasks_col = Task.get_pymongo_collection()

    # unique tasks (user, old type) if task not migrated
    old_tasks = await tasks_col.aggregate([
        {"$match": {"type": {"$exists": True}}}, # find tasks, which have type
        {"$group": {"_id": {"user": "$user", "type": "$type"}}} # group by user and type
    ])

    pairs = await old_tasks.to_list(length=None)

    migrated = 0
    for pair in pairs:
        # get user and old type
        username = pair["_id"]["user"]
        old_type = pair["_id"]["type"]

        # get title and order
        title, order, expire_days = OLD_DEFAULT_BOARDS.get(old_type, DEFAULT_BOARD)
        award = baseBoards_points.get(old_type, 0)
        board = await _get_or_create_board(
            username,
            title,
            order,
            expire_days,
            award_points=award,
            award_xp=award,
            is_weekly=old_type == "hard",
        )

        # migrate task
        result = await tasks_col.update_many(
            {"user": username, "type": old_type},
            {
                "$set": {"board_id": str(board.id)},
                "$unset": {"type": ""},
            }
        )
        migrated += result.modified_count

    logger.info("Migrated %d tasks to boards", migrated)
    await _migrate_user_completed_tasks()
    await _backfill_board_completed_tasks()
