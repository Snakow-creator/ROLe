from avatar.data import (
    AVATAR_CATALOG,
    DEFAULT_AVATAR_ID,
    ROLE_AVATAR_PAIRS,
    ROLE_RANK_BY_LEVEL,
    STARTER_AVATARS,
)


def role_avatar_ids(level, xp):
    """Include each role reached so far, with the first pair earned at positive XP."""
    if level == 1 and xp <= 0:
        return ()
    rank = ROLE_RANK_BY_LEVEL.get(level, len(ROLE_AVATAR_PAIRS))
    return tuple(
        avatar_id
        for pair in ROLE_AVATAR_PAIRS[:rank]
        for avatar_id in pair
    )


def available_avatar_ids(user):
    """Combine recorded grants with role eligibility for older accounts."""
    earned = set(user.get("unlocked_avatar_ids", ()))
    earned.update(role_avatar_ids(user["level"], user["xp"]))
    return STARTER_AVATARS.keys() | earned.intersection(AVATAR_CATALOG)


def current_avatar_id(user):
    avatar_id = user.get("current_avatar")
    return avatar_id if avatar_id in AVATAR_CATALOG else DEFAULT_AVATAR_ID


def avatar_collection(user):
    available = available_avatar_ids(user)
    return [
        {"id": avatar_id, **avatar, "available": avatar_id in available}
        for avatar_id, avatar in AVATAR_CATALOG.items()
    ]
