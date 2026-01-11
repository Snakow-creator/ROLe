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


    async def get_type_tasks(self, name):
        tasks = await self.model.find(Task.user == name).to_list()
        type_tasks = set()

        for task in tasks:
            type_tasks.add(task.type)

        return list(type_tasks)


    async def get_user_tasks_by_type(self, name, type):
        # get user tasks by filters and type
        tasks = await self.model.find(
            Task.user == name,
            Task.type == type,
            Task.completed == False,
            Task.inactive == False,
            Task.date <= datetime.now(timezone.utc),
        ).to_list()

        return tasks

    async def insert_task(self, creds, name):
        # insert task with data to mongodb
        task = self.model(
          title=creds.title,
          description=creds.description,
          type=creds.type,
          user=name,
          date=creds.date,
        )

        await task.insert()
        return task

task_repo = TaskRepository()
