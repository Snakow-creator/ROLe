from repositories import task_repo, board_repo

from datetime import datetime, timezone
from base.task_timing import expired_date_filter
from planning.service import refresh as refresh_plan


class TaskService:
    @staticmethod
    async def update(name=None, *, now=None):
        now = now or datetime.now(timezone.utc)
        await refresh_plan(name, now)

        # get inexpired boards
        boards = await board_repo.get_expire_boards(name)

        for board in boards:
            days = board["_id"]
            await task_repo.update_expired_task(
                board["board_id"], expired_date_filter(days, now)
            )
