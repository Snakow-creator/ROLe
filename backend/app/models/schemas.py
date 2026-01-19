from pydantic import BaseModel, Field
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
    type: str = Field(description="Тип квеста")
    date: Optional[datetime] = Field(description="Дата запланированного квеста")


class ItemSchema(BaseModel):
    title: str = Field(max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: str | int = Field(min_length=1, description="Цена товара")
    type: str = Field(min_length=1, max_length=20, description="Тип товара")
    min_level: str | int = Field(description="Минимальный уровень для покупки")
