from base.config import BaseRepository
from models.models import Task

from datetime import datetime, timezone


class TaskRepository(BaseRepository):
    def __init__(self):
        super().__init__(Task)

    async def get_user_tasks(self, name):
        # get user tasks by filters
        tasks = await self.model.find(
            Task.user == name,
            Task.inactive == False,
            Task.completed == False,
            Task.date <= datetime.now(timezone.utc)
            ).sort(
            -Task.date
        ).to_list()

        return tasks


    async def get_user_tasks_by_board_id(self, name, board_id):
        # get user tasks by filters and type
        tasks = await self.model.find(
            Task.user == name,
            Task.board_id == board_id,
            Task.completed == False,
            Task.inactive == False,
            Task.date <= datetime.now(timezone.utc),
        ).to_list()

        return tasks

    async def update_expired_task(self, board_id, border):
        await self.model.find(
            {
                "board_id": {"$in": board_id},
                "inactive": False,
                "completed": False,
                "date": {"$lt": border}
            }
        ).update({"$set": {"inactive": True}})


    async def insert_task(self, creds, name):
        # insert task with data to mongodb
        task = self.model(
          title=creds.title,
          description=creds.description,
          board_id=creds.board_id,
          user=name,
          date=creds.date,
        )

        await task.insert()
        return task
