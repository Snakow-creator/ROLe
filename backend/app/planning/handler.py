from datetime import date
from typing import Literal

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends

from api.core.security import security
from models.models import User
from planning import service
from planning.schemas import PlanCompletionInput, PlanEntryInput
from tasks import task_service


router = APIRouter(prefix="/plan", tags=["plan"], dependencies=[Depends(security.access_token_required)])


@router.get("")
async def get_plan(week: date | None = None, user: User = Depends(security.get_current_subject)):
    return await service.get_week(user["name"], week)


@router.post("/entries", status_code=201)
async def create_entry(data: PlanEntryInput, user: User = Depends(security.get_current_subject)):
    return await service.create_entry(user["name"], data)


@router.put("/entries/{entry_id}")
async def update_entry(entry_id: PydanticObjectId, data: PlanEntryInput, user: User = Depends(security.get_current_subject)):
    return await service.update_entry(user["name"], str(entry_id), data)


# delete entry
@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: PydanticObjectId, scope: Literal["single", "future"] = "single", user: User = Depends(security.get_current_subject)):
    await service.cancel_entry(user["name"], str(entry_id), scope)
    return {"message": "Plan entry cancelled"}


@router.post("/entries/{entry_id}/restore")
async def restore_entry(entry_id: PydanticObjectId, user: User = Depends(security.get_current_subject)):
    await service.restore_entry(user["name"], str(entry_id))
    return {"message": "Plan entry restored"}


@router.put("/entries/{entry_id}/completion")
async def set_completion(entry_id: PydanticObjectId, data: PlanCompletionInput, user: User = Depends(security.get_current_subject)):
    await task_service.update(user["name"])
    return await service.set_completion(user["name"], str(entry_id), data.completed)


@router.post("/copy")
async def copy_week(week: date, user: User = Depends(security.get_current_subject)):
    return await service.copy_next_week(user["name"], week)
