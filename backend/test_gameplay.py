import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent / "app"))

from api.core.security import security
from errors.points import NotEnoughSpointsError
from items import handler as item_handlers
from items import requests as item_requests
from levels.data import xp_list
from levels.service import LevelService
from models.schemas import ItemSchema
from tasks import requests as task_requests
from users import requests as user_requests


class Document(SimpleNamespace):
    async def update(self, changes):
        for field, value in changes.get("$inc", {}).items():
            setattr(self, field, getattr(self, field, 0) + value)
        for field, value in changes.get("$set", {}).items():
            setattr(self, field, value)


class BalanceCollection:
    """Emulate the atomic balance predicate with stale caller snapshots."""

    def __init__(self, balance):
        self.balance = balance
        self.lock = asyncio.Lock()

    async def find_one_and_update(self, query, update, **kwargs):
        async with self.lock:
            if self.balance < query["Spoints"]["$gte"]:
                return None
            previous = {"Spoints": self.balance}
            self.balance += update["$inc"]["Spoints"]
            return previous


def user(**overrides):
    data = dict(
        id="user-id", name="alice", level=1, xp=0, Spoints=0,
        mul=1, sale_shop=1, days_streak=1,
        last_streak=datetime.now(timezone.utc),
        last_mul=datetime.now(timezone.utc) - timedelta(days=7),
    )
    data.update(overrides)
    return Document(**data)


def quest(**overrides):
    data = dict(
        id="task-id", user="alice", title="Quest", board_id="board-id",
        date=datetime.now(timezone.utc) - timedelta(hours=1),
        completed=False, inactive=False, awarded_points=0,
        awarded_xp=None, is_weekly_bonus=False,
    )
    data.update(overrides)
    return Document(**data)


def setup_quest(monkeypatch, player, task, board, count=1):
    if not hasattr(board, "completed_tasks"):
        board.completed_tasks = int(task.completed)
    monkeypatch.setattr(task_requests.user_repo, "get_by_name", AsyncMock(return_value=player))
    monkeypatch.setattr(task_requests.task_repo, "get", AsyncMock(return_value=task))
    monkeypatch.setattr(task_requests.board_repo, "get", AsyncMock(return_value=board))
    monkeypatch.setattr(
        task_requests.task_repo, "get_user_tasks_by_board_id",
        AsyncMock(return_value=[task] * count),
    )


@pytest.mark.parametrize("threshold,level", xp_list)
def test_level_thresholds(threshold, level):
    assert LevelService.current(threshold) == level
    if threshold > 0:
        assert LevelService.current(threshold - 1) == level - 1


def test_level_above_last_threshold():
    assert LevelService.current(9999999) == xp_list[-1][1]


@pytest.mark.parametrize("price", [100, "100", 10.5, "10.5"])
def test_item_price_accepts_numbers_and_form_strings(price):
    item = ItemSchema(title="Item", description="", price=price, type="food", min_level="2")
    assert item.price == float(price)
    assert item.min_level == 2


@pytest.mark.parametrize("price", [0, -1, "invalid", float("nan"), float("inf")])
def test_invalid_item_prices(price):
    with pytest.raises(ValidationError):
        ItemSchema(title="Item", description="", price=price, type="food", min_level=1)


@pytest.mark.asyncio
async def test_distinct_rewards_and_undo_after_board_change(monkeypatch):
    player = user(mul=2)
    task = quest()
    board = Document(username="alice", title="Простые", award_points=20, award_xp=10, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)

    result = await task_requests.complete_task(task.id, player.name)
    assert (result["points"], result["xp"]) == (60, 30)
    assert (player.Spoints, player.xp, board.completed_tasks) == (60, 30, 1)
    assert (task.awarded_points, task.awarded_xp) == (60, 30)

    with pytest.raises(HTTPException) as error:
        await task_requests.complete_task(task.id, player.name)
    assert error.value.status_code == 409
    assert (player.Spoints, player.xp) == (60, 30)

    board.award_points = 999
    board.award_xp = 777
    player.mul = 9
    await task_requests.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, board.completed_tasks) == (0, 0, 0)
    assert not task.completed
    with pytest.raises(HTTPException) as error:
        await task_requests.uncomplete_task(task.id, player.name)
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_legacy_completed_task_without_xp_snapshot(monkeypatch):
    player = user(Spoints=20, xp=20)
    task = quest(completed=True, awarded_points=20)
    board = Document(username="alice", title="Простые", award_points=99, award_xp=1, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    await task_requests.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, board.completed_tasks) == (0, 0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("title,is_weekly", [("Трудные", False), ("Своя доска", True)])
async def test_weekly_bonus_is_saved_and_revoked(monkeypatch, title, is_weekly):
    player = user()
    task = quest()
    board = Document(username="alice", title=title, award_points=20, award_xp=10, is_weekly=is_weekly)
    setup_quest(monkeypatch, player, task, board)
    result = await task_requests.complete_task(task.id, player.name)
    assert task.is_weekly_bonus and result["is_weekly_bonus"]
    assert (player.Spoints, player.xp) == (180, 165)
    assert (player.mul, player.sale_shop) == pytest.approx((1.02, 0.985))
    assert board.completed_tasks == 1
    await task_requests.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, player.mul, player.sale_shop) == (0, 0, 1, 1)
    assert not task.is_weekly_bonus
    assert board.completed_tasks == 0


@pytest.mark.asyncio
async def test_weekly_xp_participates_in_level_up_and_undo(monkeypatch):
    player = user(xp=250)
    task = quest()
    board = Document(username="alice", title="Трудные", award_points=20, award_xp=10, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    result = await task_requests.complete_task(task.id, player.name)
    assert player.level == 2
    assert player.Spoints == 380
    assert result["isUpLevel"]
    await task_requests.uncomplete_task(task.id, player.name)
    assert (player.level, player.xp, player.Spoints) == (1, 250, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("change", [{"inactive": True}, {"date": datetime.now(timezone.utc) + timedelta(days=1)}])
async def test_inactive_or_future_task_cannot_award_points(monkeypatch, change):
    player = user()
    task = quest(**change)
    board = Document(username="alice", title="Простые", award_points=20, award_xp=20, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    with pytest.raises(HTTPException) as error:
        await task_requests.complete_task(task.id, player.name)
    assert error.value.status_code == 409
    assert (player.Spoints, player.xp) == (0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("item,status", [
    (None, 404),
    (Document(creator="bob", min_level=1), 404),
    (Document(creator="alice", min_level=10), 403),
])
async def test_purchase_rejects_unavailable_items_before_debit(monkeypatch, item, status):
    monkeypatch.setattr(item_requests.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_requests.user_repo, "get_by_name", AsyncMock(return_value=user(Spoints=1000)))
    debit = AsyncMock()
    monkeypatch.setattr(item_requests, "deprive_points_buy_item", debit)
    with pytest.raises(HTTPException) as error:
        await item_requests.buy_item("item-id", "alice")
    assert error.value.status_code == status
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_discounted_purchase_records_paid_price_and_correct_balance(monkeypatch):
    player = user(Spoints=100, sale_shop=0.985)
    item = Document(creator="alice", min_level=1, price=50, title="Item")
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_requests.user_repo.model, "get_pymongo_collection", lambda: collection)
    monkeypatch.setattr(item_requests.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_requests.user_repo, "get_by_name", AsyncMock(return_value=player))
    insert = AsyncMock()
    monkeypatch.setattr(item_requests.items_repo, "insert_item", insert)
    result = await item_requests.buy_item("item-id", "alice")
    assert player.Spoints == pytest.approx(50.75)
    insert.assert_awaited_once_with(item, "alice", price=49.25)
    assert "100" in result["notice"]["message"]
    assert "50.75" in result["notice"]["message"]


@pytest.mark.asyncio
async def test_concurrent_debits_do_not_overspend(monkeypatch):
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_requests.user_repo.model, "get_pymongo_collection", lambda: collection)
    results = await asyncio.gather(
        user_requests.deprive_points_buy_item(user(Spoints=100), 80),
        user_requests.deprive_points_buy_item(user(Spoints=100), 80),
        return_exceptions=True,
    )
    assert collection.balance == 20
    assert sum(isinstance(result, NotEnoughSpointsError) for result in results) == 1


def api_client():
    app = FastAPI()
    app.include_router(item_handlers.router)
    # AuthX creates a new closure on each access_token_required property access.
    # Override the exact dependencies captured when the routes were registered.
    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue
        for dependency in route.dependant.dependencies:
            if dependency.name == "user":
                app.dependency_overrides[dependency.call] = lambda: {"name": "alice", "level": 1}
            else:
                app.dependency_overrides[dependency.call] = lambda: None
    return TestClient(app)


def test_item_endpoints_reject_invalid_ids():
    with api_client() as client:
        assert client.put("/buy/item/invalid").status_code == 422
        assert client.delete("/delete/item/invalid").status_code == 422


@pytest.mark.parametrize("item", [None, Document(creator="bob")])
def test_delete_missing_or_foreign_item_returns_404(monkeypatch, item):
    monkeypatch.setattr(item_handlers.shop_items_repo, "get", AsyncMock(return_value=item))
    with api_client() as client:
        response = client.delete("/delete/item/0123456789abcdef01234567")
    assert response.status_code == 404


@pytest.mark.parametrize("title", ["", "   "])
def test_create_item_rejects_empty_title(title):
    with api_client() as client:
        response = client.post("/add/item", json={
            "title": title, "description": "", "price": 10, "type": "food", "min_level": 1,
        })
    assert response.status_code == 422
