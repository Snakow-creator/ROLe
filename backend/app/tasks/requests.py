from users.requests import edit_points, up_streak, edit_level
from levels import level_service
from repositories import task_repo, user_repo, board_repo
from notices import web_notice
from fastapi import HTTPException


from users import weekly_bonus
from baseTasks.data import task_bonus

from datetime import datetime, timezone, timedelta


async def complete_task(id, name):
    # find task and user
    task = await task_repo.get(id)
    user = await user_repo.get_by_name(name)
    board = await board_repo.get(task.board_id)
    if board is None or board.username != name:
        raise HTTPException(status_code=404, detail="Board not found")
    if task.completed:
        raise HTTPException(status_code=409, detail="Task already completed")
    now = datetime.now(timezone.utc)
    task_date = task.date
    if task_date is not None and task_date.tzinfo is None:
        task_date = task_date.replace(tzinfo=timezone.utc)
    if task.inactive or task_date is None or task_date > now:
        raise HTTPException(status_code=409, detail="Task is not active")
    if board.task_expire_days is not None and now >= task_date + timedelta(days=board.task_expire_days):
        await task.update({"$set": {"inactive": True}})
        raise HTTPException(status_code=409, detail="Task has expired")
    # find active user tasks by type
    tasks = await task_repo.get_user_tasks_by_board_id(name, task.board_id)
    complete_week = len(tasks) == 1 and board.is_weekly

    # points for task
    points = board.award_points * user.mul
    xp = board.award_xp * user.mul

    # check if task is last, then add bonus task
    if len(tasks) == 1:
        points = points * task_bonus
        xp = xp * task_bonus


    # update last_streak if needed
    last_streak = user.last_streak
    if isinstance(last_streak, str):
        last_streak = datetime.fromisoformat(last_streak)
    if last_streak.date() != now.date():
        await up_streak(user)

    # update user points
    await edit_points(user, points, xp)
    notice_weekly_bonus = None
    if complete_week:
        notice_weekly_bonus = await weekly_bonus.claim(user)

    # task update, do task is inactive
    await task.update(
        {"$set": {
            "completed": True,
            "complete_date": datetime.now(timezone.utc),
            "awarded_points": points,
            "awarded_xp": xp,
            "is_weekly_bonus": complete_week
        }}
    )

    fpoints = round(points, 2) # formatted points
    await board.update({"$inc": {"completed_tasks": 1}})
    fxp = round(xp, 2)

    notice = web_notice(
        title=f"Квест \"{task.title}\" выполнен!",
        message=f"Вы получили {fpoints} Spoints\n + {fxp} опыта",
        type="task_completed",
    ) # create notice

    # create data
    data = {
        "message": "Task completed",
        "isUpLevel": False,
        "points": points,
        "xp": xp,
        "notice": notice.model_dump(),
        "is_weekly_bonus": complete_week,
    }

    # update level if current level higher than task level
    current_level = level_service.current(user.xp)
    if current_level > user.level:
        previous_level = user.level
        res = await edit_level(name, current_level)

        notice_lvl = web_notice(
            title=f"Вы повысили уровень с {previous_level} до {current_level}",
            message="Вы получили бонус уровня +200 Spoints",
            type="up_level",
        )
        data["notice_up_level"] = notice_lvl.model_dump()
        data["isUpLevel"] = True
        data["spointsLevel"] = res["points"]

    # check completed hard tasks and add weekly bonus
    if notice_weekly_bonus is not None:
        data["notice_weekly_claim_bonus"] = notice_weekly_bonus.model_dump()

    return data


async def uncomplete_task(id, name):
    # find task and user
    task = await task_repo.get(id)
    user = await user_repo.get_by_name(name)
    board = await board_repo.get(task.board_id)
    if board is None or board.username != name:
        raise HTTPException(status_code=404, detail="Board not found")
    if not task.completed:
        raise HTTPException(status_code=409, detail="Task is not completed")

    points = task.awarded_points # points for completed task
    # Old completed tasks awarded the same XP and Spoints.
    xp = task.awarded_xp if task.awarded_xp is not None else points
    complete_week = task.is_weekly_bonus # check if task is weekly bonus

    fpoints = round(points, 2) # formatted points
    fxp = round(xp, 2)

    notice = web_notice(
                title=f"Квест \"{task.title}\" отменен!",
                message=f"{fpoints} Spoints и {fxp} Xp были списаны",
                type="task_uncompleted",
        )

    data = {
        "message": "Task uncompleted",
        "points": fpoints,
        "xp": fxp,
        "notice": notice.model_dump(),
    }

    # if task is weekly bonus unset bonus
    if task.is_weekly_bonus:
        notice_weekly = await weekly_bonus.revoke(user)
        complete_week = False
        data["notice_weekly_revoke_bonus"] = notice_weekly.model_dump()

    # Deprive the exact rewards saved at completion, even if the board changed.
    await edit_points(user, points, xp, o=-1)

    # task update, do task is active
    await task.update(
        {"$set": {
            "is_weekly_bonus": complete_week,
            "completed": False,
            "complete_date": None,
            "awarded_points": 0,
            "awarded_xp": 0,
        }}
    )

    await board.update({"$inc": {"completed_tasks": -1}})

    # update level if current level less than user level
    current_level = level_service.current(user.xp)
    if user.level > current_level:
        previous_level = user.level
        await edit_level(name, current_level)

        notice_lvl = web_notice(
            title=f"Вы понизили уровень с {previous_level} до {current_level}",
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
