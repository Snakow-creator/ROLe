from notices import web_notice

# notice buy item
def get_buy_item_notification(item_title: str, *, before: str, after: str, str_price: str):
    """Build a purchase notice from a title and already formatted amounts."""
    notice = web_notice(
        title=f"Вы купили \"{item_title}\" за {str_price} Spoints",
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


def error_item_notification(error_title: str):
    notice = web_notice(
        title=error_title,
        type="error",
    )

    return notice.model_dump()






