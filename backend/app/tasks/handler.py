from beanie import PydanticObjectId
from fastapi import APIRouter, Depends

from api.core.security import security
from models.models import User
from models.schemas import TaskSchema
from tasks import task_service


router = APIRouter(tags=["tasks"], dependencies=[Depends(security.access_token_required)])


@router.get("/tasks")
async def tasks(
    user: User = Depends(security.get_current_subject),
):
    return await task_service.get_tasks(user["name"])


@router.post("/add/task")
async def add_task(
    creds: TaskSchema,
    user: User = Depends(security.get_current_subject),
):
    await task_service.create_task(creds, user["name"])

    return {"message": "Task added"}


@router.put("/complete/task/{id}")
async def edit_complete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    await task_service.update(user["name"])
    return await task_service.complete_task(id, user["name"])


@router.put("/uncomplete/task/{id}")
async def edit_uncomplete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    return await task_service.uncomplete_task(id, user["name"])


@router.delete("/delete/task/{id}")
async def edit_delete_task(
    id: PydanticObjectId,
    user: User = Depends(security.get_current_subject),
):
    return await task_service.delete_task(id, user["name"])
