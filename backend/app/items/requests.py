from repositories import user_repo, shop_items_repo, items_repo

from web_notices import buy_item_notice
from users.requests import deprive_points_buy_item

from errors.points import NotEnoughSpointsError
from fastapi.responses import JSONResponse
from web_notices import error_item_notice


async def get_items(level, name):
    # get objects
    user = await user_repo.get_by_name(name)
    items_list = await shop_items_repo.get_by_min_level(level, name)

    for id in range(len(items_list)):
        stock_price = items_list[id].price
        items_list[id].price = stock_price * user.sale_shop

    return items_list


async def buy_item(id, name):
    item = await shop_items_repo.get(id) # get item
    user = await user_repo.get_by_name(name) # get user

    price = item.price * user.sale_shop # calculate price

    try:
        await deprive_points_buy_item(user, price)
    except NotEnoughSpointsError as e:
        return JSONResponse(
                status_code=402,
                content={
                    "error": "not_enough_spoints",
                    "message": str(e),
                    "notice": error_item_notice(str(e)),
                },
            )

    notice = buy_item_notice(user, price, item)

    # insert buy item in db
    await items_repo.insert_item(item, name)

    return {
            "message": f"Item {item.title} bought",
            "title": item.title,
            "notice": notice,
        }
