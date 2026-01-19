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

    # add new shop item
    async def insert_item(self, creds: dict):
        shop_item = ShopItem(
            title=creds["title"],
            description=creds["description"],
            price=creds["price"],
            creator=creds["creator"],
            type=creds["type"],
            min_level=creds["min_level"],
        )

        await self.model.insert_one(shop_item)



