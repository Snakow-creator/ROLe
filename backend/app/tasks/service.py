from repositories import task_repo

from tasks.data import tasks_expired

from datetime import datetime


class TaskService:
    @staticmethod
    async def update():
        tasks = await task_repo.find_all()

        for task in tasks:
            if tasks_expired[task.type] != None:
                if (datetime.utcnow() - task.date).days >= tasks_expired[task.type]:
                    await task.update({"$set": {"inactive": True}})
