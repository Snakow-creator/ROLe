from levels.data import which_my_role


DEFAULT_AVATAR_ID = "default_avatar_man"
_VARIANTS = {"man": "Мужской", "woman": "Женский"}
_ROLE_RANKS = {
    role: rank
    for rank, role in enumerate(dict.fromkeys(which_my_role.values()), start=1)
}
ROLE_RANK_BY_LEVEL = {level: _ROLE_RANKS[role] for level, role in which_my_role.items()}

STARTER_AVATARS = {
    f"default_avatar_{variant}": {"source": "starter", "label": f"Стартовый · {label}"}
    for variant, label in _VARIANTS.items()
}

ROLE_AVATAR_PAIRS = tuple(
    {
        f"standart_avatar{rank}_{variant}": {
            "source": "role",
            "label": f"{role} · {label}",
            "unlock_hint": "Получи первый опыт" if rank == 1 else f"Роль «{role}»",
        }
        for variant, label in _VARIANTS.items()
    }
    for role, rank in _ROLE_RANKS.items()
)

AVATAR_CATALOG = STARTER_AVATARS | {
    avatar_id: avatar
    for pair in ROLE_AVATAR_PAIRS
    for avatar_id, avatar in pair.items()
}
