from models.models import ShopItem
from base.config import BaseRepository


class ShopItemsRepository(BaseRepository):
    def __init__(self):
        super().__init__(ShopItem)

    # get items by min level
    async def get_by_min_level(self, min_level, name) -> list[ShopItem]:
        return await self.model.find(
            ShopItem.min_level <= min_level,
            ShopItem.creator == name,
        ).to_list()

    async def insert_item(self, data):
        """Insert shop item fields prepared by the item service."""
        shop_item = self.model(**data)
        return await self.model.insert_one(shop_item)

    async def delete_item(self, item):
        """Delete a previously loaded shop item."""
        await item.delete()
