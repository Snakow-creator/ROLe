from datetime import datetime, timezone

from fastapi import HTTPException
from beanie import PydanticObjectId

from base.task_timing import expired_date_filter
from levels import level_service
from tasks import requests as task_requests
from users import user_service, weekly_bonus
import planning


class TaskService:
    """Coordinate task persistence, rewards, completion and background refreshes."""

    def __init__(self, task_repo, board_repo, user_repo, planning_repository):
        self.task_repo = task_repo
        self.board_repo = board_repo
        self.user_repo = user_repo
        self.planning_repository = planning_repository

    async def create_task(self, creds, name):
        """Validate the owned board, prepare the schedule and persist the task."""
        if not PydanticObjectId.is_valid(creds.board_id):
            raise HTTPException(status_code=422, detail="Invalid board ID")
        board = await self.board_repo.get(creds.board_id)
        task_requests.validate_board_owner(board, name)
        creds = creds.model_copy(update={"board_id": str(board.id)})
        created_at = datetime.now(timezone.utc)
        data = task_requests.build_task_data(creds, name, created_at)
        return await self.task_repo.insert_task(data)

    async def get_tasks(self, name):
        """Refresh and return the user's available tasks and ordered boards."""
        await self.update(name)
        tasks = await self.task_repo.get_user_tasks(name)
        boards = await self.board_repo.get_boards(name)
        return {"message": "Success", "tasks": tasks, "boards": boards}

    async def update(self, name=None, *, now=None):
        """Refresh the plan and expire unfinished tasks whose deadlines have passed."""
        now = now or datetime.now(timezone.utc)
        await planning.planning_service.refresh(name, now)
        boards = await self.board_repo.get_expire_boards(name)
        for board in boards:
            await self.task_repo.update_expired_task(
                board["board_id"], expired_date_filter(board["_id"], now),
            )

    async def _get_owned_task(self, task_id, name):
        """Load a task and enforce the ownership rule shared by task mutations."""
        task = await self.task_repo.get(task_id)
        task_requests.validate_task_owner(task, name)
        return task

    async def _load_context(self, task_id, name):
        """Load the task, its user and its owned board for a completion change."""
        task = await self._get_owned_task(task_id, name)
        user = await self.user_repo.get_by_name(name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        board = await self.board_repo.get(task.board_id)
        task_requests.validate_board_owner(board, name)
        return task, user, board

    async def _check_completion(self, task, board, now):
        """Validate availability and mark an expired task inactive before rejecting completion."""
        task_requests.validate_completion(task, now)
        if task_requests.task_expired(task, board, now):
            await self.task_repo.update_fields(task, {"inactive": True})
            raise HTTPException(status_code=409, detail="Task has expired")

    async def _award_rewards(self, user, points, xp, weekly, now):
        """Apply streak, task rewards and an optional weekly bonus in their existing order."""
        if task_requests.needs_streak_update(user, now):
            await user_service.increment_streak(user, now)
        await user_service.change_rewards(user, points, xp)
        return await weekly_bonus.claim(user) if weekly else None

    async def _set_completion(self, task, board, *, completed, points=0, xp=0, weekly=False, now=None):
        """Save the reward snapshot and update the board's completed-task count."""
        await self.task_repo.update_fields(task, {
            "completed": completed,
            "complete_date": now if completed else None,
            "awarded_points": points,
            "awarded_xp": xp,
            "is_weekly_bonus": weekly,
        })
        await self.board_repo.change_completed_count(board, 1 if completed else -1)

    async def _adjust_level(self, user, *, completing):
        """Apply a level change in the permitted direction and return its response fields."""
        current_level = level_service.current(user.xp)
        should_change = current_level > user.level if completing else current_level < user.level
        if not should_change:
            return {}
        previous_level = user.level
        result = await user_service.set_level(user, current_level)
        notice = task_requests.level_change_notice(previous_level, current_level)
        if completing:
            return {"notice_up_level": notice, "isUpLevel": True, "spointsLevel": result["points"]}
        return {"notice_down_level": notice}

    async def complete_task(self, task_id, name):
        """Complete an available task and award its saved points, XP and optional bonuses."""
        task, user, board = await self._load_context(task_id, name)
        now = datetime.now(timezone.utc)
        await self._check_completion(task, board, now)
        remaining = await self.task_repo.get_user_tasks_by_board_id(name, task.board_id)
        points, xp, weekly = task_requests.calculate_rewards(user, board, len(remaining))
        notice_weekly = await self._award_rewards(user, points, xp, weekly, now)
        await self._set_completion(task, board, completed=True, points=points, xp=xp, weekly=weekly, now=now)
        data = task_requests.completion_response(task, points, xp, weekly)
        data.update(await self._adjust_level(user, completing=True))
        if notice_weekly is not None:
            data["notice_weekly_claim_bonus"] = notice_weekly.model_dump()
        return data

    async def uncomplete_task(self, task_id, name):
        """Undo completion using the saved rewards, even when board settings have changed."""
        task, user, board = await self._load_context(task_id, name)
        if not task.completed:
            raise HTTPException(status_code=409, detail="Task is not completed")
        points, xp = task_requests.saved_rewards(task)
        data = task_requests.uncompletion_response(task, points, xp)
        if task.is_weekly_bonus:
            notice = await weekly_bonus.revoke(user)
            data["notice_weekly_revoke_bonus"] = notice.model_dump()
        await user_service.change_rewards(user, points, xp, operation=-1)
        await self._set_completion(task, board, completed=False)
        data.update(await self._adjust_level(user, completing=False))
        return data

    async def delete_task(self, task_id, name):
        """Delete a standalone task or cancel a planned task while keeping its reward history."""
        task = await self._get_owned_task(task_id, name)
        if task.plan_entry_id:
            await self.planning_repository.update_entry(name, task.plan_entry_id, {
                "cancelled": True, "completed": task.completed, "complete_date": task.complete_date,
            })
            await self.task_repo.update_fields(task, {"inactive": True})
        else:
            await self.task_repo.delete_task(task)
        return task_requests.deletion_response(task)
