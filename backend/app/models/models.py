from pydantic import Field, ConfigDict
from beanie import Document, Indexed
from typing import Annotated, Optional

from datetime import datetime, timezone


class User(Document):
    # основные данные
    name: Annotated[str, Indexed(unique=True)] = Field(min_length=1, max_length=20, description="Имя пользователя")
    hashed_password: str
    level: int = Field(default=1, gt=0)
    xp: float = Field(default=0, ge=0)
    Spoints: float = Field(default=0, ge=0)
    # подряд завершенные дни
    days_streak: int = Field(default=0, ge=0)
    last_streak: str | datetime = datetime.now(timezone.utc)
    # множители и последний множитель
    mul: float = Field(default=1, ge=0)
    sale_shop: float = Field(default=1, ge=0)
    last_mul: datetime = datetime.now(timezone.utc)
    # последние данные множителей
    penult_mul: float = Field(default=1, ge=0)
    penult_sale_shop: float = Field(default=1, ge=0)
    penult_last_mul: datetime = datetime.now(timezone.utc)
    # завершенные задания
    complete_simple_tasks: int = Field(default=0, ge=0)
    complete_common_tasks: int = Field(default=0, ge=0)
    complete_hard_tasks: int = Field(default=0, ge=0)
    complete_expert_tasks: int = Field(default=0, ge=0)
    complete_hardcore_tasks: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "users"


class BaseTask(Document):
    difficulty: Annotated[str, Indexed(unique=True)]
    points: int = Field(ge=0, description="Поинты за задание")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "baseTasks"


class Level(Document):
    level: Annotated[int, Indexed(unique=True)]
    xp: int = Field(ge=0, description="Требуемый опыт")
    role: str = Field(description="Роль пользователя")

    class Settings:
        name = "levels"


class ShopItem(Document):
    title: str = Field(max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: int = Field(gt=0, description="Цена товара")
    creator: str = Field(min_length=1, description="Пользователь, который создал товар")
    type: str = Field(min_length=1, max_length=20,description="Тип товара")
    min_level: int = Field(gte=0, description="Минимальный уровень для покупки")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "shop_items"


class Item(Document):
    title: str = Field(max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: int = Field(gt=0, description="Цена товара")
    name: str = Field(description="Пользователь, который купил товар")
    date: Optional[datetime] = datetime.now(timezone.utc)

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "items"


class Task(Document):
    # основные данные
    title: str = Field(min_length=1, max_length=100, description="Название квеста")
    description: str = Field(max_length=255, description="Описание квеста")
    type: str = Field(description="Тип квеста")
    user: str = Field(description="Пользователь, который зарегистрировал квест")
    # дата создания и завершения
    date: Optional[datetime] = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    complete_date: Optional[datetime] = Field(
        default=None, description="Дата завершения квеста"
    )
    # пройдена ли задание или истекло
    completed: bool = Field(default=False, description="Завершен квест")
    inactive: bool = Field(default=False, description="Истекло время квеста")
    # получен ли недельный бонус
    is_weekly_bonus: bool = Field(default=False, description="Недельный бонус")
    # сколько начислено поинтов за задание(если было выполнено)
    awarded_points: float = Field(default=0, ge=0, description="Поинты за квест")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "tasks"
