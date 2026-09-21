from users.requests import edit_points, up_streak, edit_level
from levels import level_service
from repositories import task_repo, user_repo
from notices import web_notice


from users import weekly_bonus
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

    fpoints = round(points, 2) # formatted points

    notice = web_notice(
        title=f"Квест \"{task.title}\" выполнен!",
        message=f"Вы получили {fpoints} Spoints\n + {fpoints} опыта",
        type="task_completed",
    ) # create notice

    # create data
    data = {
        "message": "Task completed",
        "isUpLevel": False,
        "points": points,
        "xp": points,
        "notice": notice.model_dump(),
        "is_weekly_bonus": False,
    }

    # update level if current level higher than task level
    current_level = level_service.current(user.xp)
    if current_level > user.level:
        res = await edit_level(name, current_level)

        notice_lvl = web_notice(
            title=f"Вы повысили уровень с {user.level} до {current_level}",
            message="Вы получили бонус уровня +200 Spoints",
            type="up_level",
        )
        data["notice_up_level"] = notice_lvl.model_dump()
        data["isUpLevel"] = True
        data["spointsLevel"] = res["points"]

    # check completed hard tasks and add weekly bonus
    if len(tasks) == 1 and task.type == "hard":
        notice_weekly_bonus = await weekly_bonus.claim(user)
        data["is_weekly_bonus"] = True
        data["notice_weekly_claim_bonus"] = notice_weekly_bonus.model_dump()

    return data


async def uncomplete_task(id, name):
    # find task and user
    task = await task_repo.get(id)
    user = await user_repo.get_by_name(name)

    points = task.awarded_points # points for completed task
    complete_week = task.is_weekly_bonus # check if task is weekly bonus

    fpoints = round(points, 2) # formatted points

    notice = web_notice(
                title=f"Квест \"{task.title}\" отменен!",
                message=f"{fpoints} Spoints и {fpoints} Xp были списаны",
                type="task_uncompleted",
        )

    data = {
        "message": "Task uncompleted",
        "points": fpoints,
        "xp": fpoints,
        "notice": notice.model_dump(),
    }

    # if task is weekly bonus unset bonus
    if task.is_weekly_bonus:
        notice_weekly = await weekly_bonus.revoke(user)
        complete_week = False
        data["notice_weekly_revoke_bonus"] = notice_weekly.model_dump()

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
    current_level = level_service.current(user.xp)
    if user.level > current_level:
        await edit_level(name, current_level)

        notice_lvl = web_notice(
            title=f"Вы понизили уровень с {user.level} до {current_level}",
            message="Бонус уровня +200 Spoints был списан",
            type="down_level",
        )

        data["notice_down_level"] = notice_lvl.model_dump()

    return data


async def delete_task(task):
    notice = web_notice(
        title=f"Задача {task.title} удалена",
        type="delete_task"
    )

    return {
        "message": "Task deleted",
        "title": task.title,
        "notice": notice.model_dump(),
    }
