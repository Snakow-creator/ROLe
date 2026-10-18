from datetime import datetime, timezone

from fastapi import HTTPException

from base.task_timing import utc_datetime
from errors.points import NotEnoughSpointsError
from users import requests as user_requests


class UserService:
    """Coordinate user rewards, streaks and account data through the user repository."""

    def __init__(self, repository):
        self.repository = repository

    async def load_data(self, name):
        """Load a user and format their account data for login."""
        user = await self.repository.get_by_name(name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user_requests.profile_data(user)

    async def refresh_expired_bonuses(self, now=None):
        """Reset expired streaks and multipliers while leaving recent users unchanged."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        for user in await self.repository.find_all():
            values = user_requests.expired_bonus_fields(user, now)
            if values:
                await self.repository.update_user(user, values=values)

    async def set_level(self, user, level):
        """Set the level and award or revoke its balance bonus using the loaded user."""
        points = user_requests.level_reward_points(user, level)
        await self.repository.update_user(user, values={"level": level}, increments={"Spoints": points})
        return {"message": "Success", "points": abs(points)}

    async def change_rewards(self, user, points, xp, *, operation=1):
        """Add or revoke the supplied points and XP amounts."""
        await self.repository.update_user(user, increments={"Spoints": operation * points, "xp": operation * xp})

    async def debit_purchase(self, user, price):
        """Debit a purchase atomically and return the balance before payment."""
        previous = await self.repository.debit_purchase(user.id, price)
        if previous is None:
            raise NotEnoughSpointsError
        user.Spoints = previous["Spoints"] - price
        return previous["Spoints"]

    async def increment_streak(self, user, now=None):
        """Increment the streak and record its latest update timestamp."""
        now = utc_datetime(now or datetime.now(timezone.utc))
        await self.repository.update_user(user, values={"last_streak": now}, increments={"days_streak": 1})
