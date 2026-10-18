from base.config import BaseRepository
from models.models import User
from pymongo import ReturnDocument


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    async def get_by_name(self, name) -> User:
        """Find a user by their unique name."""
        return await self.find_one(User.name == name)

    async def insert_user(self, name, hashed_password):
        """Insert a user with an already hashed password."""
        user = self.model(name=name, hashed_password=hashed_password)
        await user.insert()
        return user

    async def update_user(self, user, *, values=None, increments=None):
        """Apply supplied field values and numeric increments to a loaded user."""
        changes = {}
        if values:
            changes["$set"] = values
        if increments:
            changes["$inc"] = increments
        if changes:
            await user.update(changes)

    async def debit_purchase(self, user_id, price):
        """Debit only a sufficient balance and return the document before payment."""
        return await self.model.get_pymongo_collection().find_one_and_update(
            {"_id": user_id, "Spoints": {"$gte": price}},
            {"$inc": {"Spoints": -price}}, return_document=ReturnDocument.BEFORE,
        )

    async def refund_purchase(self, user_id, price):
        """Add back a failed purchase's price without replacing concurrent balance changes."""
        user = await self.model.get_pymongo_collection().find_one_and_update(
            {"_id": user_id}, {"$inc": {"Spoints": price}},
            return_document=ReturnDocument.AFTER,
        )
        if user is None:
            raise RuntimeError("Could not refund purchase: user not found")

    async def get_all_names(self):
        """Return user names without loading complete user documents."""
        return await self.model.get_pymongo_collection().distinct("name")
