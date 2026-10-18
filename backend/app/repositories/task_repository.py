from base.config import BaseRepository
from models.models import Task

from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError


class TaskRepository(BaseRepository):
    def __init__(self):
        super().__init__(Task)

    async def get_plan_tasks_by_board(self, board_id, name):
        """Return the user's board quests linked to plan entries, including completed ones."""
        return await self.model.get_pymongo_collection().find({
            "board_id": str(board_id), "user": name, "plan_entry_id": {"$type": "string"},
        }).to_list(length=None)

    async def delete_by_board(self, board_id, name):
        """Delete all of the user's tasks on a board and return their count."""
        result = await self.model.get_pymongo_collection().delete_many({
            "board_id": str(board_id), "user": name,
        })
        return result.deleted_count

    @staticmethod
    def _active_filter(name):
        """Select the user's unfinished, active tasks whose scheduled time has arrived."""
        return {
            "user": name, "inactive": False, "completed": False,
            "date": {"$lte": datetime.now(timezone.utc)},
        }

    async def get_user_tasks(self, name):
        """Return currently available tasks, newest first."""
        return await self.model.find(self._active_filter(name)).sort("-date").to_list()

    async def get_user_tasks_by_board_id(self, name, board_id):
        """Return currently available tasks on the requested board."""
        query = {**self._active_filter(name), "board_id": board_id}
        return await self.model.find(query).to_list()

    async def update_expired_task(self, board_id, date_filter):
        """Mark unfinished tasks selected by the service's deadline filter as inactive."""
        await self.model.find(
            {
                "board_id": {"$in": board_id},
                "inactive": False,
                "completed": False,
                "date": date_filter
            }
        ).update({"$set": {"inactive": True}})

    async def insert_task(self, data):
        """Insert task fields prepared by the task service."""
        task = self.model(**data)
        await task.insert()
        return task

    async def update_fields(self, task, values):
        """Update fields on a previously loaded task document."""
        await task.update({"$set": values})

    async def delete_task(self, task):
        """Delete a previously loaded standalone task."""
        await task.delete()

    async def get_quest(self, user, entry_id):
        """Find the user's quest linked to the given plan entry."""
        return await self.model.get_pymongo_collection().find_one({"user": user, "plan_entry_id": str(entry_id)})

    async def get_quests(self, user, entry_ids):
        """Return the user's quests linked to the given plan entry IDs."""
        return await self.model.get_pymongo_collection().find({
            "user": user, "plan_entry_id": {"$in": entry_ids},
        }).to_list(length=None)

    async def deactivate_quests(self, user, entry_id):
        """Mark the user's quests linked to the given plan entry as inactive."""
        return await self.model.get_pymongo_collection().update_many(
            {"plan_entry_id": str(entry_id), "user": user}, {"$set": {"inactive": True}},
        )

    async def delete_uncompleted_quests(self, user, entry_id):
        """Delete uncompleted quests for the user's entry while preserving completed quests."""
        return await self.model.get_pymongo_collection().delete_many({
            "plan_entry_id": str(entry_id), "user": user, "completed": False,
        })

    async def update_uncompleted_quest(self, user, entry_id, fields):
        """Update the user's linked quest only if it has not been completed."""
        return await self.model.get_pymongo_collection().update_one(
            {"plan_entry_id": str(entry_id), "user": user, "completed": False}, {"$set": fields},
        )

    async def insert_quest_if_missing(self, quest):
        """Insert a quest for the plan entry if missing without overwriting an existing quest."""
        query = {"plan_entry_id": quest["plan_entry_id"], "user": quest["user"]}
        try:
            return await self.model.get_pymongo_collection().update_one(query, {"$setOnInsert": quest}, upsert=True)
        except DuplicateKeyError:
            pass
