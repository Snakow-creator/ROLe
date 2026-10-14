from beanie import PydanticObjectId as ObjectId

from base.config import BaseRepository
from models.models import Board


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


