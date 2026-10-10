from beanie import PydanticObjectId as ObjectId

from base.config import BaseRepository
from models.models import Board


class BoardRepository(BaseRepository):
    def __init__(self):
        super().__init__(Board)

    async def get_boards(self, name):
        # get boards and sort by order
        boards = await self.model.find(
            Board.username == name
        ).to_list()

        boards.sort(key=lambda x: x.order)

        return boards

    async def get_award_by_board(self, board_id):
        # get board by id
        return await self.model.get(ObjectId(board_id))

    async def get_expire_boards(self):
        # get boards with expire days
        return await self.model.aggregate([
            {"$match": {"expire_days": {"$ne": None}}},
            {"$group": {
                "_id": "$expire_days",
                "board_id": {"$push": {"$toString": "$_id"}}
            }}
        ]).to_list()


