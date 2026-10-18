from datetime import date
from typing import Literal

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends

from api.core.security import security
from models.models import User
from planning import planning_service
from planning.schemas import PlanCompletionInput, PlanEntryInput
from tasks import task_service


router = APIRouter(prefix="/plan", tags=["plan"], dependencies=[Depends(security.access_token_required)])


# get weekly plan
@router.get("")
async def get_plan(week: date | None = None, user: User = Depends(security.get_current_subject)):
    return await planning_service.get_weekly_plan(user["name"], week)


# create entry
@router.post("/entries", status_code=201)
async def create_entry(data: PlanEntryInput, user: User = Depends(security.get_current_subject)):
    return await planning_service.create_entry(user["name"], data)


# update entry
@router.put("/entries/{entry_id}")
async def update_entry(entry_id: PydanticObjectId, data: PlanEntryInput, user: User = Depends(security.get_current_subject)):
    return await planning_service.update_entry(user["name"], str(entry_id), data)


# delete entry
@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: PydanticObjectId, scope: Literal["single", "future"] = "single", user: User = Depends(security.get_current_subject)):
    await planning_service.cancel_entry(user["name"], str(entry_id), scope)
    return {"message": "Plan entry cancelled"}


# restore entry
@router.post("/entries/{entry_id}/restore")
async def restore_entry(entry_id: PydanticObjectId, user: User = Depends(security.get_current_subject)):
    await planning_service.restore_entry(user["name"], str(entry_id))
    return {"message": "Plan entry restored"}


# complete entry
@router.put("/entries/{entry_id}/completion")
async def set_completion(entry_id: PydanticObjectId, data: PlanCompletionInput, user: User = Depends(security.get_current_subject)):
    await task_service.update(user["name"])
    return await planning_service.set_completion(user["name"], str(entry_id), data.completed)


# copy plan
@router.post("/copy")
async def copy_week(week: date, user: User = Depends(security.get_current_subject)):
    return await planning_service.copy_next_week(user["name"], week)
