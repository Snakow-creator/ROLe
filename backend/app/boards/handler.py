from fastapi import APIRouter, Depends

from api.core.security import security
from models.schemas import BoardCreateSchema
from repositories import board_repo


router = APIRouter(tags=["boards"])


@router.post(
    "/add/board",
    status_code=201,
    dependencies=[Depends(security.access_token_required)],
)
async def add_board(
    creds: BoardCreateSchema,
    user=Depends(security.get_current_subject),
):
    board = await board_repo.insert_board(creds, user["name"])
    return {"message": "Board added", "board": board}
