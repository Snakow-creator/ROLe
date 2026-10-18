from beanie import PydanticObjectId as ObjectId

from base.config import BaseRepository
from models.models import Board


class BoardRepository(BaseRepository):
    def __init__(self):
        super().__init__(Board)

    async def count_user_boards(self, name):
        """Count the user's boards without loading their documents."""
        return await self.model.get_pymongo_collection().count_documents({"username": name})

    async def insert_board(self, data):
        """Insert board fields prepared by the board service."""
        board = self.model(**data)
        await board.insert()
        return board

    async def get_owned_board(self, board_id, name):
        """Find a board by ID only among the user's boards."""
        return await self.model.get_pymongo_collection().find_one({
            "_id": ObjectId(board_id), "username": name,
        })

    async def delete_board(self, board_id, name):
        """Delete an owned board and report whether it was removed."""
        result = await self.model.get_pymongo_collection().delete_one({
            "_id": ObjectId(board_id), "username": name,
        })
        return bool(result.deleted_count)

    async def compact_order(self, name, after_order):
        """Shift the user's subsequent board positions down by one."""
        return await self.model.get_pymongo_collection().update_many(
            {"username": name, "order": {"$gt": after_order}}, {"$inc": {"order": -1}},
        )

    async def change_completed_count(self, board, amount):
        """Adjust a loaded board's completed-task count."""
        await board.update({"$inc": {"completed_tasks": amount}})

    async def get_board_documents(self, name):
        """Return the user's board documents for building the weekly plan."""
        return await self.model.get_pymongo_collection().find({"username": name}).to_list(length=None)

    async def get_boards(self, name):
        # get boards and sort by order
        boards = await self.model.find(
            Board.username == name
        ).to_list()

        boards.sort(key=lambda x: (x.order, str(x.id)))

        return boards

    async def get_expire_boards(self, name=None):
        # get boards with expire days
        query = {"task_expire_days": {"$type": "number", "$gte": 0}}
        if name is not None:
            query["username"] = name
        return await self.model.aggregate([
            {"$match": query},
            {"$group": {
                "_id": "$task_expire_days",
                "board_id": {"$push": {"$toString": "$_id"}}
            }}
        ]).to_list()


