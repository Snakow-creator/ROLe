from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.core.security import security
from avatar.avatars import available_avatar_ids, avatar_collection, current_avatar_id
from levels.data import which_my_role
from repositories import board_repo, user_repo


router = APIRouter(prefix="/profile", tags=["profile"])


class AvatarSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avatar_id: str = Field(min_length=1, max_length=50)


@router.get("")
async def profile(
    user: dict = Depends(security.get_current_subject),
):
    try:
        return {
            "name": user["name"],
            "level": user["level"],
            "role": which_my_role.get(user["level"], "Бог"),
            "avatar": current_avatar_id(user),
            "avatars": avatar_collection(user),
            "xp": user["xp"],
            "Spoints": user["Spoints"],
            "days_streak": user["days_streak"],
            "mul": user["mul"],
            "sale_shop": user["sale_shop"],
            "last_streak": user["last_streak"],
            "last_mul": user["last_mul"],
            "boards": [
                {
                    "_id": str(board.id),
                    "title": board.title,
                    "completed_tasks": board.completed_tasks,
                }
                for board in await board_repo.get_boards(user["name"])
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Not authorized") from exc


@router.put("/avatar")
async def select_avatar(
    selection: AvatarSelection,
    user: dict = Depends(security.get_current_subject),
):
    if selection.avatar_id not in available_avatar_ids(user):
        raise HTTPException(status_code=403, detail="Avatar is unavailable")
    if not await user_repo.set_avatar(user["_id"], selection.avatar_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"avatar": selection.avatar_id}
