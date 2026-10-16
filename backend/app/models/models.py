from pydantic import Field, ConfigDict
from beanie import Document, Indexed
from pymongo import IndexModel, ASCENDING
from typing import Annotated, Optional

from datetime import datetime, timezone


class User(Document):
    # основные данные
    name: Annotated[str, Indexed(unique=True)] = Field(min_length=1, max_length=20, description="Имя пользователя")
    hashed_password: str
    current_avatar: str = Field(default="avatar_default_1", min_length=1, max_length=50, description="ID аватара")
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
    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "users"


class UsersAvatars(Document):
    user_name: str = Field(min_length=1, max_length=20, description="Имя пользователя")
    avatar_id: str = Field(min_length=1, max_length=50, description="ID аватара")
    created_at: datetime = datetime.now(timezone.utc)

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "users_avatars"
        indexes = [
            IndexModel(
                [("user_name", 1), ("avatar_id", 1)],
                unique=True
            )
        ]


class Level(Document):
    level: Annotated[int, Indexed(unique=True)]
    xp: int = Field(ge=0, description="Требуемый опыт")
    role: str = Field(description="Роль пользователя")

    class Settings:
        name = "levels"


class ShopItem(Document):
    title: str = Field(max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: float = Field(gt=0, allow_inf_nan=False, description="Цена товара")
    creator: str = Field(min_length=1, description="Пользователь, который создал товар")
    type: str = Field(min_length=1, max_length=20,description="Тип товара")
    min_level: int = Field(ge=0, description="Минимальный уровень для покупки")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "shop_items"


class Item(Document):
    title: str = Field(max_length=100, description="Название товара")
    description: str = Field(max_length=255, description="Описание товара")
    price: float = Field(ge=0, allow_inf_nan=False, description="Цена товара")
    name: str = Field(description="Пользователь, который купил товар")
    date: Optional[datetime] = datetime.now(timezone.utc)

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "items"


# old tasks data:
# type - type of board
# change type -> board_id
class Task(Document):
    # основные данные
    title: str = Field(min_length=1, max_length=100, description="Название квеста")
    description: str = Field(max_length=255, description="Описание квеста")
    board_id: str = Field(min_length=1, max_length=50, description="ID канбана")
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
    awarded_xp: float | None = Field(default=None, ge=0, description="Начисленный опыт за квест")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "tasks"
        indexes = [IndexModel([("user", ASCENDING), ("board_id", ASCENDING), ("position", ASCENDING)])]


class Notice(Document):
    name: str = Field(min_length=1, max_length=50, description="ID пользователя")
    id: int = Field(gt=0, description="ID уведомления", unique=True)
    message: str = Field(min_length=1, max_length=255, description="Текст уведомления")
    hidden: bool = Field(default=False, description="Скрыть уведомление")
    if_bonus: bool = Field(default=False, description="Бонус")
    id_bonus: str = Field(default=None, description="ID бонуса")

    date: Optional[datetime] = datetime.now(timezone.utc)


    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "notices"



class Avatar_Item(Document):
    id_avatar: str = Field(min_length=1, max_length=50, description="ID аватара")
    name_user: str = Field(min_length=1, description="Пользователь, который купил аватар")
    date: Optional[datetime] = datetime.now(timezone.utc) # дата приобретения

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "avatar_items"


class Board(Document):
    username: str = Field(min_length=1, max_length=20, description="Имя пользователя")
    title: str = Field(min_length=1, max_length=100, description="Название канбана")
    order: int = Field(default=0, description="Порядок отображения")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    award_points: int = Field(default=0, ge=0, description="Поинты канбана")
    award_xp: int = Field(default=0, ge=0, description="Опыт канбана")
    completed_tasks: int = Field(default=0, ge=0, description="Количество выполненных квестов")
    is_weekly: bool = Field(default=False, description="Есть ли недельный бонус")
    task_expire_days: int | None = Field(default=None, ge=0, description="Дни на выполнение квеста")

    model_config = ConfigDict(extra="forbid")

    class Settings:
        name = "boards"
        indexes = [
            IndexModel([("username", ASCENDING), ("order", ASCENDING)]),
        ]
