from fastapi import APIRouter, Depends
from beanie import PydanticObjectId
from fastapi.responses import JSONResponse

from models.models import User
from models.schemas import ItemSchema

from api.core.security import security
from items import item_service
from items.requests import insufficient_balance_data
from errors.points import NotEnoughSpointsError


router = APIRouter(tags=['items'])


@router.get('/items', dependencies=[Depends(security.access_token_required)])
async def list_items(
    user: User = Depends(security.get_current_subject)
):
    return await item_service.get_items(user['level'], user['name'])


@router.put('/buy/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_buy_item(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    try:
        return await item_service.buy_item(id, user['name'])
    except NotEnoughSpointsError as exc:
        return JSONResponse(status_code=402, content=insufficient_balance_data(str(exc)))


@router.post('/add/item', dependencies=[Depends(security.access_token_required)])
async def handler_add_item(
    creds: ItemSchema,
    user: User = Depends(security.get_current_subject),
):
    return await item_service.add_item(creds, user["name"])


@router.delete('/delete/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_delete_item(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    return await item_service.delete_item(id, user["name"])


