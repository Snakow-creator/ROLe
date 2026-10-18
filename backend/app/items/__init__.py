from items.service import ItemService
from repositories import user_repo, shop_items_repo, items_repo


item_service = ItemService(user_repo, shop_items_repo, items_repo)
