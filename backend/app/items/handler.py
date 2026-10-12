from fastapi import APIRouter, Depends
from beanie import PydanticObjectId
from fastapi.exceptions import HTTPException

from models.models import User
from models.schemas import ItemSchema

from api.core.security import security
from repositories import shop_items_repo
from items.requests import get_items, buy_item
from web_notices import create_item_notice, delete_item_notice


router = APIRouter(tags=['items'])


@router.get('/items', dependencies=[Depends(security.access_token_required)])
async def list_items(
    user: User = Depends(security.get_current_subject)
):
    return await get_items(user['level'], user['name'])


@router.put('/buy/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_buy_item(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject
)):
    return await buy_item(id, user['name'])


@router.post('/add/item', dependencies=[Depends(security.access_token_required)])
async def handler_add_item(
    creds: ItemSchema,
    user: User = Depends(security.get_current_subject),
):
    title = creds.title.strip()
    if not title:
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid title", "field": "title", "error": "Invalid title"}
        )

    data = {
        "creator": user["name"],
        "title": title,
        "type": creds.type,
        "description": creds.description,
        "price": creds.price,
        "min_level": max(1, creds.min_level),
    }

    # insert item and send notice
    await shop_items_repo.insert_item(data)
    notice = create_item_notice(creds)

    return {"message": "Item added", "notice": notice}


@router.delete('/delete/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_delete_item(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    shop_item = await shop_items_repo.get(id)

    if shop_item is None or shop_item.creator != user['name']:
        raise HTTPException(status_code=404, detail="Item not found")


    await shop_item.delete()
    notice = delete_item_notice(shop_item)

    return {"message": "Item deleted", "notice": notice}


