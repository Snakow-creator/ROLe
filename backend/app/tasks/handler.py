from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from models.schemas import TaskSchema
from models.models import PlanEntry, Task, User
from beanie import PydanticObjectId

from tasks.requests import complete_task, uncomplete_task, delete_task
from tasks import task_service

from repositories import task_repo, board_repo
from api.core.security import security


router = APIRouter(tags=["tasks"])


@router.get("/tasks", dependencies=[Depends(security.access_token_required)])
async def tasks(
    user: User = Depends(security.get_current_subject),
):

    await task_service.update(user["name"])
    tasks = await task_repo.get_user_tasks(user["name"])
    boards = await board_repo.get_boards(user["name"])

    return {"message": "Success", "tasks": tasks, "boards": boards}


@router.post("/add/task", dependencies=[Depends(security.access_token_required)])
async def add_task(
    creds: TaskSchema,
    user: User = Depends(security.get_current_subject),
):
    if not PydanticObjectId.is_valid(creds.board_id):
        raise HTTPException(status_code=422, detail="Invalid board ID")
    board = await board_repo.get(creds.board_id)
    if board is None or board.username != user["name"]:
        raise HTTPException(status_code=404, detail="Board not found")
    creds = creds.model_copy(update={"board_id": str(board.id)})
    await task_repo.insert_task(creds, user["name"])

    return {"message": "Task added"}


@router.put("/complete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def edit_complete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    await task_service.update(user["name"])
    task = await task_repo.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    res = await complete_task(id, user["name"])
    return res


@router.put("/uncomplete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def edit_uncomplete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    task = await task_repo.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    res = await uncomplete_task(id, user["name"])
    return res


@router.delete("/delete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def edit_delete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    task = await task_repo.get(id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    if task.plan_entry_id:
        # Keep the occurrence as a cancelled snapshot; the scheduler must not recreate it.
        await PlanEntry.get_pymongo_collection().update_one(
            {"_id": PydanticObjectId(task.plan_entry_id), "user": user["name"]},
            {"$set": {"cancelled": True, "completed": task.completed, "complete_date": task.complete_date}},
        )
        # Retain the reward snapshot, so restoring a planned quest cannot award it twice.
        await task.update({"$set": {"inactive": True}})
    else:
        await task.delete()
    res = await delete_task(task)
    return res

