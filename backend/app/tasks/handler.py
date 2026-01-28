from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from models.schemas import TaskSchema
from models.models import Task, User

from tasks.requests import complete_task, uncomplete_task

from repositories import task_repo, base_tasks_repo
from baseTasks.data import list_baseTasks
from api.core.security import security

import logging


router = APIRouter(tags=["tasks"])


@router.get("/tasks", dependencies=[Depends(security.access_token_required)])
async def tasks(
    user: User = Depends(security.get_current_subject),
):
    tasks = await task_repo.get_user_tasks(user["name"])
    type_tasks = await base_tasks_repo.get_base_tasks(user['name'])

    return {"message": "Success", "tasks": tasks, "type_tasks": type_tasks}


@router.post("/add/task", dependencies=[Depends(security.access_token_required)])
async def add_task(
    creds: TaskSchema,
    user: User = Depends(security.get_current_subject),
):
    if creds.type not in list_baseTasks:
        raise HTTPException(status_code=400, detail="Invalid task type")

    await task_repo.insert_task(creds, user["name"])

    return {"message": "Task added"}


@router.put("/complete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def edit_task(
    id: str,
    user: User = Depends(security.get_current_subject),
):
    task = await task_repo.get(id)

    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    res = await complete_task(id, user["name"])
    return res


@router.put("/uncomplete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def edit_task(
    id: str,
    user: User = Depends(security.get_current_subject),
):
    task = await task_repo.get(id)
    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    res = await uncomplete_task(id, user["name"])
    return res


@router.delete("/delete/task/{id}", dependencies=[Depends(security.access_token_required)])
async def delete_task(
    id: str,
    user: User = Depends(security.get_current_subject),
):
    task = await task_repo.get(id)
    if task.user != user["name"]:
        raise HTTPException(status_code=401, detail="Unauthorized, this task is not your")

    await task.delete()
    return {"message": "Task deleted", "title": task.title}

