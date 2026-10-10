# migrations/boards.py
import logging

from models.models import Board, Task

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

async def _get_or_create_board(
    username: str, title: str, order: int, expire_days: int | None = None
):
    board = await Board.find_one(Board.username == username, Board.title == title)
    if not board:
        board = Board(
            username=username,
            title=title,
            order=order,
        )
        await board.insert()
        logger.info("Created board '%s' for user %s", title, username)
    return board

async def migrate_tasks_to_boards():
    tasks_col = Task.get_pymongo_collection()

    # unique tasks (user, old type) if task not migrated
    old_tasks = await tasks_col.aggregate([
        {"$match": {"type": {"$exists": True}}}, # find tasks, which have type
        {"$group": {"_id": {"user": "$user", "type": "$type"}}} # group by user and type
    ])

    pairs = await old_tasks.to_list(length=None)

    # return if no tasks to migrate
    if not pairs:
        return

    migrated = 0
    for pair in pairs:
        # get user and old type
        username = pair["_id"]["user"]
        old_type = pair["_id"]["type"]

        # get title and order
        title, order, expire_days = OLD_DEFAULT_BOARDS.get(old_type, DEFAULT_BOARD)
        board = await _get_or_create_board(username, title, order, expire_days)

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
