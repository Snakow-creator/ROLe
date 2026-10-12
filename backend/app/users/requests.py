from repositories import user_repo
from baseTasks.data import list_baseTasks
from datetime import datetime, timezone
from pymongo import ReturnDocument

from errors.points import NotEnoughSpointsError


async def users_days_and_last_mul_expired():
    # get users
    users = await user_repo.find_all()

    for user in users:
        # expire days streak
        if (datetime.utcnow() - user.last_streak).days >= 1 and user.days_streak != 1:
            await user.update({"$set": {"days_streak": 1}})

        # expire last_mul
        if (datetime.utcnow() - user.last_mul).days >= 14 and user.mul != 1:
            await user.update({"$set": {"mul": 1, "sale_shop": 1}})


async def edit_level(name, level):
    # edit user level
    user = await user_repo.get_by_name(name)

    # add points * n if up level more than 1
    # if level - user.level > 0 -> up level
    # if level - user.level < 0 -> deprive
    points = (level - user.level) * 200

    await user.update(
        {
            "$inc": {"Spoints": points},
            "$set": {"level": level},
        }
    )

    return {"message": "Success", "points": abs(points)}


async def edit_points(user, points, xp, o=1):
    # update user points, xp and complete tasks
    # user - object User
    # o - operation + or -, add or deprive

    increments = {"Spoints": o * points, "xp": o * xp}
    await user.update({"$inc": increments})

async def deprive_points_buy_item(user, points):
    # deprive user points by buy item
    # if points doesn't enough raise

    collection = user_repo.model.get_pymongo_collection()
    previous = await collection.find_one_and_update(
        {"_id": user.id, "Spoints": {"$gte": points}},
        {"$inc": {"Spoints": -points}},
        return_document=ReturnDocument.BEFORE,
    )
    if previous is None:
        raise NotEnoughSpointsError
    user.Spoints = previous["Spoints"] - points
    return previous["Spoints"]


async def up_streak(user):
    await user.update(
        {
            "$set": {
                "last_streak": datetime.now(timezone.utc),
            },
            "$inc": {"days_streak": 1},
        }
    )

