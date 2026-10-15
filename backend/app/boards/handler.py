from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId

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


@router.delete(
    "/delete/board/{id}",
    dependencies=[Depends(security.access_token_required)],
)
async def delete_board(
    id: PydanticObjectId,
    user=Depends(security.get_current_subject),
):
    result = await board_repo.delete_board(id, user["name"])
    if result is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return {"message": "Board deleted", "board_id": str(id), **result}
