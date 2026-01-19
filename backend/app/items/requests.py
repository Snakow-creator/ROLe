from repositories import user_repo, shop_items_repo, items_repo


async def get_items(level, name):
    # get objects
    user = await user_repo.get_by_name(name)
    items_list = await shop_items_repo.get_by_min_level(level, name)

    for id in range(len(items_list)):
        stock_price = items_list[id].price
        items_list[id].price = stock_price * user.sale_shop

    return items_list


async def buy_item(id, name):
    item = await shop_items_repo.get(id)
    user = await user_repo.get_by_name(name)

    price = -item.price * user.sale_shop

    await user.update({
        "$inc": {
            "Spoints": price
        }
    })

    # insert buy item in db
    await items_repo.insert_item(item, name)

    return {"message": f"Вы купили \"{item.title}\" за {abs(price)} Spoints", "title": item.title}
