"""Pure user data formatting and bonus-expiration calculations."""

from base.dates.calendar import as_utc_datetime


LEVEL_REWARD = 200


def profile_data(user):
    """Build the account data used in the login response."""
    return {
        "name": user.name,
        "level": user.level,
        "xp": user.xp,
        "Spoints": user.Spoints,
        "days_streak": user.days_streak,
        "mul": user.mul,
        "sale_shop": user.sale_shop,
        "last_streak": as_utc_datetime(user.last_streak).timestamp(),
        "last_mul": as_utc_datetime(user.last_mul).timestamp(),
    }


def expired_bonus_fields(user, now):
    """Select streak and multiplier resets using the existing one-day and fourteen-day limits."""
    fields = {}
    if (now - as_utc_datetime(user.last_streak)).days >= 1 and user.days_streak != 1:
        fields["days_streak"] = 1
    if (now - as_utc_datetime(user.last_mul)).days >= 14 and user.mul != 1:
        fields.update(mul=1, sale_shop=1)
    return fields


def level_reward_points(user, level):
    """Calculate the signed balance adjustment for changing the user's level."""
    return (level - user.level) * LEVEL_REWARD
