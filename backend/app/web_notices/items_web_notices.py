from notices import web_notice

from base.format import fmt_points

# notice buy item
def get_buy_item_notification(user, price, item):

    # format data
    before = fmt_points(user.Spoints)
    after = fmt_points(user.Spoints - price)
    str_price = fmt_points(abs(price))

    notice = web_notice(
        title=f"Вы купили \"{item.title}\" за {str_price} Spoints",
        message=f"Ваш баланс изменен с {before} на {after}",
        type="buy_item",
    )

    return notice.model_dump()


# notice create item
def get_create_item_notification(creds):
    notice = web_notice(
        title=f"Вы создали товар или услугу \"{creds.title}\"",
        type="create_item",
    )

    return notice.model_dump()


def get_delete_item_notification(item):
    notice = web_notice(
        title=f"Вы удалили товар или услугу \"{item.title}\"",
        type="delete_item",
    )

    return notice.model_dump()






