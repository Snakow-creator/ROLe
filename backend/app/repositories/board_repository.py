from beanie import PydanticObjectId as ObjectId

from base.config import BaseRepository
from models.models import Board, Task


class BoardRepository(BaseRepository):
    def __init__(self):
        super().__init__(Board)

    async def insert_board(self, creds, name):
        boards = await self.get_boards(name)
        order = len(boards)
        board = self.model(
            **creds.model_dump(),
            username=name,
            order=order,
        )
        await board.insert()
        return board

    async def delete_board(self, board_id, name):
        boards = self.model.get_pymongo_collection()
        query = {"_id": ObjectId(board_id), "username": name}
        board = await boards.find_one(query)
        if board is None:
            return None

        # Keep the board available for retry if task cleanup fails. The default
        # standalone MongoDB installation does not support transactions.
        result = await Task.get_pymongo_collection().delete_many({
            "board_id": str(board_id), "user": name,
        })
        deleted = await boards.delete_one(query)
        if deleted.deleted_count:
            await boards.update_many(
                {"username": name, "order": {"$gt": board.get("order", 0)}},
                {"$inc": {"order": -1}},
            )
        return {"title": board["title"], "deleted_tasks": result.deleted_count}

    async def get_boards(self, name):
        # get boards and sort by order
        boards = await self.model.find(
            Board.username == name
        ).to_list()

        boards.sort(key=lambda x: (x.order, str(x.id)))

        return boards

    async def get_award_by_board(self, board_id):
        # get board by id
        return await self.model.get(ObjectId(board_id))

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


