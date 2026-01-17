from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from models.models import User
from models.schemas import ItemSchema

from api.core.security import security
from repositories import shop_items_repo
from items.requests import get_items, buy_item


router = APIRouter(tags=['items'])


@router.get('/items', dependencies=[Depends(security.access_token_required)])
async def list_items(
    user: User = Depends(security.get_current_subject)
):
    return await get_items(user['level'], user['name'])


@router.put('/buy/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_buy_item(
    id: str,
    user: User = Depends(security.get_current_subject
)):
    return await buy_item(id, user['name'])


@router.post('/add/item', dependencies=[Depends(security.access_token_required)])
async def handler_add_item(
    creds: ItemSchema,
    user: User = Depends(security.get_current_subject),
):
    if creds.title == "":
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid title", "field": "title", "error": "Invalid title"}
        )

    try:
        data = {
            "creator": user["name"],
            "title": creds.title,
            "type": creds.type,
            "description": creds.description,
            "price": float(creds.price),
            "min_level": int(creds.min_level)
        }
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=422,
            content={"message": "Invalid price or float", "error": "Invalid price or float"}
        )

    if data["price"] <= 0:
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid price", "field": "price", "error": "Invalid price"}
        )

    await shop_items_repo.insert_item(data)

    return {"message": "Item added"}


@router.delete('/delete/item/{id}', dependencies=[Depends(security.access_token_required)])
async def handler_delete_item(
    id: str,
    user: User = Depends(security.get_current_subject),
):
    shop_item = await shop_items_repo.get(id)

    if shop_item.creator != user['name']:
        raise JSONResponse(
            status_code=401,
            content={"message": "Unauthorized name", "error": "Unauthorized name"}
        )

    await shop_items_repo.delete(id)

    return {"message": "Item deleted"}


