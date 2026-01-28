from users.requests import edit_points, up_streak, edit_level
from levels.hooks import current_level
from repositories import task_repo, user_repo

from tasks.utils import weekly_bonus, unset_weekly_bonus
from baseTasks.data import baseTasks_points, task_bonus

from datetime import datetime, timezone


async def complete_task(id, name):
    # find task and user
    task = await task_repo.get(id)
    user = await user_repo.get_by_name(name)
    # find active user tasks by type
    tasks = await task_repo.get_user_tasks_by_type(name, task.type)

    complete_week = False


    # points for task
    points = baseTasks_points[task.type] * user.mul

    # check if task is last, then add bonus task
    if len(tasks) == 1:
        points = points * task_bonus

    # check completed hard tasks and add weekly bonus
    if len(tasks) == 1 and task.type == "hard":
        await weekly_bonus(user)
        complete_week = True


    # update last_streak if needed
    last_streak = user.last_streak.strftime("%Y-%m-%d")
    if last_streak != datetime.now().strftime("%Y-%m-%d"):
        await up_streak(user)

    # update user points
    await edit_points(user, points, task.type)

    # task update, do task is inactive
    await task.update(
        {"$set": {
            "completed": True,
            "complete_date": datetime.now(timezone.utc),
            "awarded_points": points,
            "is_weekly_bonus": complete_week
        }}
    )

    # update level if current level higher than task level
    level = current_level(user.xp)
    if level > user.level:
        res = await edit_level(name, level)
        return {
            "message": "Task completed",
            "isWeekly": True,
            "points": points,
            "xp": points,
            "spointsLevel": res["points"],
        }

    return {
        "message": "Task completed",
        "isUpLevel": False,
        "points": points,
        "xp": points,
        "isWeekly": complete_week
    }


async def uncomplete_task(id, name):
    # find task and user
    task = await task_repo.get(id)
    user = await user_repo.get_by_name(name)

    points = task.awarded_points
    complete_week = task.is_weekly_bonus

    # if task is weekly bonus unset bonus
    if task.is_weekly_bonus:
        await unset_weekly_bonus(user)
        complete_week = False

    # task update, do task is active
    await task.update(
        {"$set": {
            "is_weekly_bonus": complete_week,
            "completed": False,
            "complete_date": None,
            "awarded_points": 0
        }}
    )

    # deprive user points
    await edit_points(user, points, task.type, -1)


    # update level if current level less than user level
    level = current_level(user.xp)
    if user.level > level:
        await edit_level(name, level)

    return {"message": "Task uncompleted", "points": points, "xp": points}
