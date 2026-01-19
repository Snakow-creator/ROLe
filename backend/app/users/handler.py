from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from api.core.security import security
from models.models import User


router = APIRouter(tags=["users"], prefix="/users")


@router.get("/avatar", dependencies=[Depends(security.access_token_required)])
async def get_users(
    user: User = Depends(security.get_current_subject),
):
    try:
      return user["current_avatar"]

    except:
       raise HTTPException(
          status_code=404,
          detail={"error": "Not authorized"}
       )
