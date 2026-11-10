from avatar.avatars import role_avatar_ids
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
        values = values or {}
        increments = increments or {}
        changes = {}
        if values:
            changes["$set"] = values
        if increments:
            changes["$inc"] = increments
        if "level" in values or increments.get("xp"):
            level = values.get("level", user.level)
            xp = user.xp + increments.get("xp", 0)
            earned = set(user.unlocked_avatar_ids)
            grants = [avatar_id for avatar_id in role_avatar_ids(level, xp) if avatar_id not in earned]
            if grants:
                changes["$addToSet"] = {"unlocked_avatar_ids": {"$each": grants}}
        if changes:
            await user.update(changes)

    async def set_avatar(self, user_id, avatar_id):
        result = await self.model.get_pymongo_collection().update_one(
            {"_id": user_id}, {"$set": {"current_avatar": avatar_id}},
        )
        return result.matched_count > 0

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
