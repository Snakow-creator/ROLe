from datetime import datetime, timezone

from notices import web_notice


class WeeklyBonusService:
    """Apply weekly rewards and restore the previous multiplier settings on undo."""

    POINTS = 150
    XP = 150
    MULTIPLIER = 1.02
    DISCOUNT = 0.985

    def __init__(self, repository):
        self.repository = repository

    def _notice(self, user, *, claimed):
        """Build the notification after the user's weekly bonus has changed."""
        mul, sale = round(user.mul, 2), round(user.sale_shop, 2)
        if claimed:
            title, kind = "Вы получили недельный бонус! 🎉", "claim_weekly_bonus"
            message = f"Ваш множитель опыта теперь снова {mul}%, а скидка магазина {sale}%, а Xp и Spoints увеличены на 150"
        else:
            title, kind = "Ваш бонус недели снят", "revoke_weekly_bonus"
            message = f"Ваш множитель опыта теперь снова {mul}%, а скидка магазина {sale}%, а Xp и Spoints вернулись на прежний уровень"
        return web_notice(title=title, message=message, type=kind)

    async def claim(self, user):
        """Save the previous settings, then add rewards and improve the multipliers."""
        await self.repository.update_user(user, values={
            "penult_mul": user.mul,
            "penult_sale_shop": user.sale_shop,
            "penult_last_mul": user.last_mul,
            "last_mul": datetime.now(timezone.utc),
            "mul": user.mul * self.MULTIPLIER,
            "sale_shop": user.sale_shop * self.DISCOUNT,
        }, increments={"Spoints": self.POINTS, "xp": self.XP})
        return self._notice(user, claimed=True)

    async def revoke(self, user):
        """Remove the weekly rewards and restore the saved multiplier settings."""
        await self.repository.update_user(user, values={
            "last_mul": user.penult_last_mul,
            "mul": user.penult_mul,
            "sale_shop": user.penult_sale_shop,
        }, increments={"Spoints": -self.POINTS, "xp": -self.XP})
        return self._notice(user, claimed=False)
