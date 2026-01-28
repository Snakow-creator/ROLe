from base.config import BaseRepository
from beanie.operators import In
from models.models import BaseTask

from tasks.data import tasks_sort


class BaseTaskRepository(BaseRepository):
    def __init__(self):
        super().__init__(BaseTask)

    async def get_base_tasks(self, name):
        # get base_tasks by user and base task for all
        tasks = await self.model.find(
          In(BaseTask.creator, ["all", name])
        ).to_list()

        base_tasks = [task.difficulty for task in tasks]

        base_tasks.sort(key=lambda x: tasks_sort[x])

        return base_tasks
