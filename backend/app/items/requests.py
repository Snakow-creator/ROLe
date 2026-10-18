"""Validation, data preparation and response formatting for shop items."""

from fastapi import HTTPException
from beanie import PydanticObjectId as ObjectId

from base.format import fmt_points
from web_notices import buy_item_notice, error_item_notice


def discounted_items(items, discount):
    """Return item copies with discounted prices, preserving the source documents."""
    return [item.model_copy(update={"price": item.price * discount}) for item in items]


def validate_item_owner(item, name):
    """Reject missing items and items owned by another user."""
    if item is None or item.creator != name:
        raise HTTPException(status_code=404, detail="Item not found")


def validate_purchase(user, item, name):
    """Check that the user exists, owns the item and meets its level requirement."""
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    validate_item_owner(item, name)
    if user.level < item.min_level:
        raise HTTPException(status_code=403, detail="Not enough level")


def build_item_data(creds, name):
    """Prepare item fields with a trimmed title and a minimum level of one."""
    title = creds.title.strip()
    if not title:
        raise HTTPException(
            status_code=422,
            detail={"message": "Invalid title", "field": "title", "error": "Invalid title"},
        )
    return {
        "creator": name,
        "title": title,
        "type": creds.type,
        "description": creds.description,
        "price": creds.price,
        "min_level": max(1, creds.min_level),
    }


def build_purchase_data(item, name, price):
    """Prepare a purchase with a stable ID for verifying the result of a failed write."""
    return {
        "_id": ObjectId(),
        "title": item.title,
        "description": item.description,
        "price": price,
        "name": name,
    }


def insufficient_balance_data(message):
    """Build error data without choosing an HTTP response type or status."""
    return {
        "error": "not_enough_spoints",
        "message": message,
        "notice": error_item_notice(message),
    }


def purchase_response(user, item, price, balance_before):
    """Build a purchase response using the actual paid price and previous balance."""
    before = fmt_points(user.Spoints + price if balance_before is None else balance_before)
    after = fmt_points(user.Spoints)
    str_price = fmt_points(abs(price))
    return {
        "message": f"Item {item.title} bought",
        "title": item.title,
        "notice": buy_item_notice(item.title, before=before, after=after, str_price=str_price),
    }
