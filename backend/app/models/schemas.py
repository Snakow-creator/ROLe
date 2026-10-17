from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class UserSchema(BaseModel):
    name: str = Field(max_length=20, description="Имя пользователя")
    password: str = Field(min_length=8, max_length=20, description="Пароль пользователя")


class RegisterUserSchema(BaseModel):
    name: str = Field(max_length=20, description="Имя пользователя")
    password1: str = Field(min_length=8, max_length=20, description="Пароль")
    password2: str = Field(min_length=8, max_length=20, description="Подтвердите пароль")


class TaskSchema(BaseModel):
    title: str = Field(max_length=100, description="Название квеста")
    description: str = Field(max_length=255, description="Описание квеста")
    board_id: str = Field(min_length=1, max_length=50, description="ID канбана")
    date: Optional[datetime] = Field(default=None, description="Дата запланированного квеста")


class BoardCreateSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100, description="Название доски")
    award_points: int = Field(default=0, ge=0, strict=True, description="Очки за квест")
    award_xp: int = Field(default=0, ge=0, strict=True, description="Опыт за квест")
    is_weekly: bool = Field(default=False, strict=True, description="Есть ли недельный бонус")
    task_expire_days: int | None = Field(default=None, gt=0, le=36500, strict=True, description="Дни на выполнение квеста")

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ItemSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: float = Field(gt=0, allow_inf_nan=False, description="Цена товара")
    type: str = Field(min_length=1, max_length=20, description="Тип товара")
    min_level: int = Field(ge=0, description="Минимальный уровень для покупки")
