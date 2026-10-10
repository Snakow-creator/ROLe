from repositories import task_repo, board_repo

from datetime import datetime, timezone


class TaskService:
    @staticmethod
    async def update():
        now = datetime.now(timezone.utc)

        # get inexpired boards
        boards = await board_repo.get_expire_boards()

        for board in boards:
            days = board["_id"]
            border = now - datetime.timedelta(days=days)

            await task_repo.update_expired_task(board["board_id"], border)
