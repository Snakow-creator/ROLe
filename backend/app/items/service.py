from errors.items import PurchaseStatusUnknownError
from items import requests as item_requests
from users import user_service
from web_notices import create_item_notice, delete_item_notice


class ItemService:
    """Coordinate shop operations through the supplied repositories."""

    def __init__(self, user_repo, shop_items_repo, items_repo):
        self.user_repo = user_repo
        self.shop_items_repo = shop_items_repo
        self.items_repo = items_repo

    async def get_items(self, level, name):
        """Load the user's shop items and apply their current discount."""
        user = await self.user_repo.get_by_name(name)
        items = await self.shop_items_repo.get_by_min_level(level, name)
        return item_requests.discounted_items(items, user.sale_shop)

    async def _purchase_exists(self, purchase_id):
        """Verify persistence without treating a failed verification as a rejected write."""
        try:
            return await self.items_repo.exists(purchase_id)
        except Exception as exc:
            raise PurchaseStatusUnknownError("Could not verify whether the purchased item was saved") from exc

    async def _save_purchase(self, user, item, price):
        """Save a purchase and accept a failed acknowledgement only when its record exists."""
        data = item_requests.build_purchase_data(item, user.name, price)
        try:
            await self.items_repo.insert_item(data)
        except Exception:
            if not await self._purchase_exists(data["_id"]):
                raise

    async def _record_purchase(self, user, item, price):
        """Debit the balance and refund only a confirmed failure to save the purchase."""
        balance_before = await user_service.debit_purchase(user, price)
        try:
            await self._save_purchase(user, item, price)
        except PurchaseStatusUnknownError:
            # Preserve the debit until an uncertain write can be reconciled.
            raise
        except Exception:
            await self.user_repo.refund_purchase(user.id, price)
            user.Spoints += price
            raise
        return balance_before

    async def buy_item(self, id, name):
        """Validate a purchase, debit the balance and record the paid price."""
        item = await self.shop_items_repo.get(id)
        user = await self.user_repo.get_by_name(name)
        item_requests.validate_purchase(user, item, name)
        price = item.price * user.sale_shop
        balance_before = await self._record_purchase(user, item, price)
        return item_requests.purchase_response(user, item, price, balance_before)

    async def add_item(self, creds, name):
        """Validate and insert a shop item, then return its creation notice."""
        data = item_requests.build_item_data(creds, name)
        await self.shop_items_repo.insert_item(data)
        return {"message": "Item added", "notice": create_item_notice(creds)}

    async def delete_item(self, id, name):
        """Delete a shop item owned by the user and return its deletion notice."""
        item = await self.shop_items_repo.get(id)
        item_requests.validate_item_owner(item, name)
        await self.shop_items_repo.delete_item(item)
        return {"message": "Item deleted", "notice": delete_item_notice(item)}
