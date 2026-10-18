from base.config import BaseRepository
from models.models import Item
from beanie import PydanticObjectId as ObjectId
from pymongo.errors import ConnectionFailure, ExecutionTimeout, WriteConcernError

from errors.items import PurchaseStatusUnknownError


class ItemsRepository(BaseRepository):
    def __init__(self):
        super().__init__(Item)

    async def insert_item(self, data):
        """Insert a purchased item, marking write timeouts as uncertain outcomes."""
        item = self.model(**data)
        try:
            await item.insert()
        except (ConnectionFailure, ExecutionTimeout, WriteConcernError, TimeoutError) as exc:
            raise PurchaseStatusUnknownError("The purchase write may still complete") from exc
        return item

    async def exists(self, item_id):
        """Check whether an item with the supplied ID is stored."""
        return await self.model.get_pymongo_collection().find_one({"_id": ObjectId(item_id)}) is not None

    async def get_user_items(self, name):
        """Return purchased items belonging to the user, newest first."""
        return await self.model.find(
            self.model.name == name
        ).sort(-self.model.date).to_list()


