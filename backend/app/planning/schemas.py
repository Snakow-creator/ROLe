from datetime import date
from typing import Literal

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PlanEntryInput(BaseModel):
    kind: Literal["task", "goal"] = "task"
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=255)
    day: date
    time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    board_id: str | None = None
    goal_id: str | None = None
    repeat: bool = Field(default=True, strict=True)
    scope: Literal["single", "future"] = "single"

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("board_id", "goal_id")
    @classmethod
    def valid_reference(cls, value):
        if value is not None:
            if not PydanticObjectId.is_valid(value):
                raise ValueError("Invalid reference ID")
            return str(PydanticObjectId(value))
        return value

    @model_validator(mode="after")
    def valid_fields(self):
        if self.end_time and (not self.time or self.end_time <= self.time):
            raise ValueError("End time must follow start time")
        if self.kind == "goal" and any([self.time, self.end_time, self.board_id, self.goal_id]):
            raise ValueError("Weekly goals cannot have a time, board or parent goal")
        return self


class PlanCompletionInput(BaseModel):
    completed: bool = Field(strict=True)
    model_config = ConfigDict(extra="forbid")
