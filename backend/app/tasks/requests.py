"""Pure validation, reward calculations and response data for tasks."""

from datetime import datetime

from fastapi import HTTPException

from base.task_timing import scheduled_datetime, task_deadline, utc_datetime
from boards.data import task_bonus
from notices import web_notice


def build_task_data(creds, name, created_at):
    """Prepare task content and schedule using the server's creation timestamp."""
    return {
        "title": creds.title,
        "description": creds.description,
        "board_id": creds.board_id,
        "user": name,
        "created_at": created_at,
        "date": scheduled_datetime(creds.date) if creds.date is not None else created_at,
    }


def validate_task_owner(task, name):
    """Reject missing tasks and tasks belonging to another user."""
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user != name:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")


def validate_board_owner(board, name):
    """Require an existing board owned by the task's user."""
    if board is None or board.username != name:
        raise HTTPException(status_code=404, detail="Board not found")


def validate_completion(task, now):
    """Reject repeated completion and tasks that are inactive or not yet scheduled."""
    if task.completed:
        raise HTTPException(status_code=409, detail="Task already completed")
    task_date = utc_datetime(task.date) if task.date is not None else None
    if task.inactive or task_date is None or task_date > now:
        raise HTTPException(status_code=409, detail="Task is not active")


def task_expired(task, board, now):
    """Check expiration using the same deadline rule as background updates."""
    deadline = task_deadline(utc_datetime(task.date), board.task_expire_days)
    return deadline is not None and now >= deadline


def calculate_rewards(user, board, remaining_tasks):
    """Calculate separate points and XP, including the last-task multiplier."""
    last_task = remaining_tasks == 1
    points, xp = board.award_points * user.mul, board.award_xp * user.mul
    if last_task:
        points *= task_bonus
        xp *= task_bonus
    return points, xp, last_task and board.is_weekly


def saved_rewards(task):
    """Read the awarded snapshot, keeping compatibility with legacy tasks without saved XP."""
    points = task.awarded_points
    xp = task.awarded_xp if task.awarded_xp is not None else points
    return points, xp


def needs_streak_update(user, now):
    """Check whether the user's last streak update belongs to another date."""
    last_streak = user.last_streak
    if isinstance(last_streak, str):
        last_streak = datetime.fromisoformat(last_streak)
    return last_streak.date() != now.date()


def completion_response(task, points, xp, weekly):
    """Build the completion response using the actual awarded amounts."""
    notice = web_notice(
        title=f'Квест "{task.title}" выполнен!',
        message=f"Вы получили {round(points, 2)} Spoints\n + {round(xp, 2)} опыта",
        type="task_completed",
    )
    return {
        "message": "Task completed", "isUpLevel": False,
        "points": points, "xp": xp, "notice": notice.model_dump(),
        "is_weekly_bonus": weekly,
    }


def uncompletion_response(task, points, xp):
    """Build the undo response using the saved rewards rather than current board settings."""
    points, xp = round(points, 2), round(xp, 2)
    notice = web_notice(
        title=f'Квест "{task.title}" отменен!',
        message=f"{points} Spoints и {xp} Xp были списаны",
        type="task_uncompleted",
    )
    return {"message": "Task uncompleted", "points": points, "xp": xp, "notice": notice.model_dump()}


def level_change_notice(previous_level, current_level):
    """Build a level-up or level-down notice without changing user data."""
    if current_level > previous_level:
        title = f"Вы повысили уровень с {previous_level} до {current_level}"
        message, kind = "Вы получили бонус уровня +200 Spoints", "up_level"
    else:
        title = f"Вы понизили уровень с {previous_level} до {current_level}"
        message, kind = "Бонус уровня +200 Spoints был списан", "down_level"
    return web_notice(title=title, message=message, type=kind).model_dump()


def deletion_response(task):
    """Build a notice for a task whose deletion has already been processed."""
    notice = web_notice(title=f"Задача {task.title} удалена", type="delete_task")
    return {"message": "Task deleted", "title": task.title, "notice": notice.model_dump()}
