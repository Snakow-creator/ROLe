import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import AutoReconnect

from api.core.security import security
from errors.points import NotEnoughSpointsError
from errors.items import PurchaseStatusUnknownError
from items import handler as item_handlers
from items import item_service
from levels.data import xp_list
from levels.service import LevelService
from models.schemas import ItemSchema
from models.models import ShopItem
from tasks import task_service
from users import user_service


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
            if "Spoints" in query and self.balance < query["Spoints"]["$gte"]:
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
    if not hasattr(board, "task_expire_days"):
        board.task_expire_days = None
    if not hasattr(board, "completed_tasks"):
        board.completed_tasks = int(task.completed)
    monkeypatch.setattr(task_service.user_repo, "get_by_name", AsyncMock(return_value=player))
    monkeypatch.setattr(task_service.task_repo, "get", AsyncMock(return_value=task))
    monkeypatch.setattr(task_service.board_repo, "get", AsyncMock(return_value=board))
    monkeypatch.setattr(
        task_service.task_repo, "get_user_tasks_by_board_id",
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

    result = await task_service.complete_task(task.id, player.name)
    assert (result["points"], result["xp"]) == (60, 30)
    assert (player.Spoints, player.xp, board.completed_tasks) == (60, 30, 1)
    assert (task.awarded_points, task.awarded_xp) == (60, 30)

    with pytest.raises(HTTPException) as error:
        await task_service.complete_task(task.id, player.name)
    assert error.value.status_code == 409
    assert (player.Spoints, player.xp) == (60, 30)

    board.award_points = 999
    board.award_xp = 777
    player.mul = 9
    await task_service.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, board.completed_tasks) == (0, 0, 0)
    assert not task.completed
    with pytest.raises(HTTPException) as error:
        await task_service.uncomplete_task(task.id, player.name)
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_legacy_completed_task_without_xp_snapshot(monkeypatch):
    player = user(Spoints=20, xp=20)
    task = quest(completed=True, awarded_points=20)
    board = Document(username="alice", title="Простые", award_points=99, award_xp=1, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    await task_service.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, board.completed_tasks) == (0, 0, 0)


@pytest.mark.asyncio
async def test_weekly_board_bonus_and_level_change_are_reversible(monkeypatch):
    player = user(xp=250)
    task = quest()
    board = Document(username="alice", title="My weekly board", award_points=20, award_xp=10, is_weekly=True)
    setup_quest(monkeypatch, player, task, board)
    result = await task_service.complete_task(task.id, player.name)
    assert result["isUpLevel"] and result["is_weekly_bonus"]
    assert (player.level, player.xp, player.Spoints) == (2, 415, 380)
    assert result["notice_up_level"]["type"] == "up_level"
    assert result["notice_weekly_claim_bonus"]["type"] == "claim_weekly_bonus"

    result = await task_service.uncomplete_task(task.id, player.name)
    assert (player.level, player.xp, player.Spoints) == (1, 250, 0)
    assert result["notice_down_level"]["type"] == "down_level"
    assert result["notice_weekly_revoke_bonus"]["type"] == "revoke_weekly_bonus"
    assert board.completed_tasks == 0
    assert (task.awarded_points, task.awarded_xp, task.completed) == (0, 0, False)


@pytest.mark.asyncio
@pytest.mark.parametrize("task,status", [(None, 404), (quest(user="bob"), 401)])
async def test_task_service_rejects_missing_or_foreign_tasks_before_rewards(monkeypatch, task, status):
    monkeypatch.setattr(task_service.task_repo, "get", AsyncMock(return_value=task))
    lookup_user = AsyncMock()
    monkeypatch.setattr(task_service.user_repo, "get_by_name", lookup_user)
    with pytest.raises(HTTPException) as error:
        await task_service.complete_task("task-id", "alice")
    assert error.value.status_code == status
    lookup_user.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("title,is_weekly", [("Трудные", True), ("Своя доска", True)])
async def test_weekly_bonus_is_saved_and_revoked(monkeypatch, title, is_weekly):
    player = user()
    task = quest()
    board = Document(username="alice", title=title, award_points=20, award_xp=10, is_weekly=is_weekly)
    setup_quest(monkeypatch, player, task, board)
    result = await task_service.complete_task(task.id, player.name)
    assert task.is_weekly_bonus and result["is_weekly_bonus"]
    assert (player.Spoints, player.xp) == (180, 165)
    assert (player.mul, player.sale_shop) == pytest.approx((1.02, 0.985))
    assert board.completed_tasks == 1
    await task_service.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, player.mul, player.sale_shop) == (0, 0, 1, 1)
    assert not task.is_weekly_bonus
    assert board.completed_tasks == 0


@pytest.mark.asyncio
async def test_weekly_xp_participates_in_level_up_and_undo(monkeypatch):
    player = user(xp=250)
    task = quest()
    board = Document(username="alice", title="Трудные", award_points=20, award_xp=10, is_weekly=True)
    setup_quest(monkeypatch, player, task, board)
    result = await task_service.complete_task(task.id, player.name)
    assert player.level == 2
    assert player.Spoints == 380
    assert result["isUpLevel"]
    await task_service.uncomplete_task(task.id, player.name)
    assert (player.level, player.xp, player.Spoints) == (1, 250, 0)


@pytest.mark.asyncio
async def test_board_title_does_not_enable_weekly_bonus(monkeypatch):
    player = user()
    task = quest()
    board = Document(username="alice", title="Трудные", award_points=20, award_xp=10, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    result = await task_service.complete_task(task.id, player.name)
    assert not task.is_weekly_bonus and not result["is_weekly_bonus"]
    assert (player.Spoints, player.xp, player.mul, player.sale_shop) == (30, 15, 1, 1)
    await task_service.uncomplete_task(task.id, player.name)
    assert (player.Spoints, player.xp, player.mul, player.sale_shop) == (0, 0, 1, 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("change", [{"inactive": True}, {"date": datetime.now(timezone.utc) + timedelta(days=1)}])
async def test_inactive_or_future_task_cannot_award_points(monkeypatch, change):
    player = user()
    task = quest(**change)
    board = Document(username="alice", title="Простые", award_points=20, award_xp=20, is_weekly=False)
    setup_quest(monkeypatch, player, task, board)
    with pytest.raises(HTTPException) as error:
        await task_service.complete_task(task.id, player.name)
    assert error.value.status_code == 409
    assert (player.Spoints, player.xp) == (0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("item,status", [
    (None, 404),
    (Document(creator="bob", min_level=1), 404),
    (Document(creator="alice", min_level=10), 403),
])
async def test_purchase_rejects_unavailable_items_before_debit(monkeypatch, item, status):
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=user(Spoints=1000)))
    debit = AsyncMock()
    monkeypatch.setattr(user_service, "debit_purchase", debit)
    with pytest.raises(HTTPException) as error:
        await item_service.buy_item("item-id", "alice")
    assert error.value.status_code == status
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_discounted_purchase_records_paid_price_and_correct_balance(monkeypatch):
    player = user(Spoints=100, sale_shop=0.985)
    item = Document(creator="alice", min_level=1, price=50, title="Item", description="")
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_service.repository.model, "get_pymongo_collection", lambda: collection)
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=player))
    insert = AsyncMock()
    monkeypatch.setattr(item_service.items_repo, "insert_item", insert)
    result = await item_service.buy_item("item-id", "alice")
    assert player.Spoints == pytest.approx(50.75)
    insert.assert_awaited_once()
    purchase = insert.await_args.args[0]
    assert purchase["price"] == 49.25
    assert purchase["name"] == "alice"
    assert purchase["title"] == item.title
    assert purchase["_id"] is not None
    assert "100" in result["notice"]["message"]
    assert "50.75" in result["notice"]["message"]


@pytest.mark.asyncio
async def test_concurrent_debits_do_not_overspend(monkeypatch):
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_service.repository.model, "get_pymongo_collection", lambda: collection)
    results = await asyncio.gather(
        user_service.debit_purchase(user(Spoints=100), 80),
        user_service.debit_purchase(user(Spoints=100), 80),
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
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
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


def test_create_item_saves_normalized_data_and_returns_notice(monkeypatch):
    insert = AsyncMock()
    monkeypatch.setattr(item_service.shop_items_repo, "insert_item", insert)
    with api_client() as client:
        response = client.post("/add/item", json={
            "title": "  Coffee  ", "description": "Break", "price": 10,
            "type": "food", "min_level": 0,
        })
    assert response.status_code == 200
    assert response.json()["message"] == "Item added"
    assert response.json()["notice"]["type"] == "create_item"
    insert.assert_awaited_once_with({
        "creator": "alice", "title": "Coffee", "description": "Break",
        "price": 10, "type": "food", "min_level": 1,
    })


def test_delete_owned_item_deletes_document_and_returns_notice(monkeypatch):
    item = Document(creator="alice", title="Coffee", delete=AsyncMock())
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    with api_client() as client:
        response = client.delete("/delete/item/0123456789abcdef01234567")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted"
    assert response.json()["notice"]["type"] == "delete_item"
    item.delete.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_listing_items_does_not_apply_discount_twice(monkeypatch):
    item = ShopItem.model_construct(
        title="Coffee", description="", price=50, creator="alice", type="food", min_level=1,
    )
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=user(sale_shop=0.985)))
    monkeypatch.setattr(item_service.shop_items_repo, "get_by_min_level", AsyncMock(return_value=[item]))
    first = await item_service.get_items(1, "alice")
    second = await item_service.get_items(1, "alice")
    assert first[0].price == second[0].price == 49.25
    assert item.price == 50
    assert first[0] is not item


def test_insufficient_balance_stays_an_http_concern(monkeypatch):
    item = Document(creator="alice", min_level=1, price=50, title="Item", description="")
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=user()))
    monkeypatch.setattr(user_service, "debit_purchase", AsyncMock(side_effect=NotEnoughSpointsError()))
    insert = AsyncMock()
    monkeypatch.setattr(item_service.items_repo, "insert_item", insert)
    with api_client() as client:
        response = client.put("/buy/item/0123456789abcdef01234567")
    assert response.status_code == 402
    assert response.json()["error"] == "not_enough_spoints"
    assert response.json()["notice"]["type"] == "error"
    insert.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("concurrent_spend", [0, 7])
async def test_failed_purchase_refunds_without_overwriting_concurrent_spending(monkeypatch, concurrent_spend):
    player = user(Spoints=100)
    item = Document(creator="alice", min_level=1, price=50, title="Item", description="")
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_service.repository.model, "get_pymongo_collection", lambda: collection)
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=player))

    async def failed_insert(*args, **kwargs):
        collection.balance -= concurrent_spend
        raise RuntimeError("write rejected")

    monkeypatch.setattr(item_service.items_repo, "insert_item", failed_insert)
    monkeypatch.setattr(item_service.items_repo, "exists", AsyncMock(return_value=False))
    with pytest.raises(RuntimeError, match="write rejected"):
        await item_service.buy_item("item-id", "alice")
    assert collection.balance == 100 - concurrent_spend


@pytest.mark.asyncio
async def test_uncertain_purchase_write_does_not_trigger_a_refund(monkeypatch):
    player = user(Spoints=100)
    item = Document(creator="alice", min_level=1, price=50, title="Item", description="")
    collection = BalanceCollection(100)
    monkeypatch.setattr(user_service.repository.model, "get_pymongo_collection", lambda: collection)
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=player))
    monkeypatch.setattr(item_service.items_repo, "insert_item", AsyncMock(side_effect=PurchaseStatusUnknownError()))
    monkeypatch.setattr(item_service.items_repo, "exists", AsyncMock(return_value=False))
    refund = AsyncMock()
    monkeypatch.setattr(item_service.user_repo, "refund_purchase", refund)
    with pytest.raises(PurchaseStatusUnknownError):
        await item_service.buy_item("item-id", "alice")
    assert collection.balance == 50
    refund.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("saved,read_fails", [(True, False), (False, False), (False, True)])
async def test_purchase_checks_uncertain_write_outcome(monkeypatch, saved, read_fails):
    model = item_service.items_repo.model
    state = {}

    async def insert(document):
        if saved:
            state["document"] = document.model_dump(by_alias=True)
        raise AutoReconnect("write acknowledgement lost")

    async def find_one(query):
        if read_fails:
            raise AutoReconnect("verification unavailable")
        document = state.get("document")
        if document is not None:
            assert query == {"_id": document["_id"]}
        return document

    monkeypatch.setattr(model, "insert", insert)
    monkeypatch.setattr(model, "get_pymongo_collection", classmethod(lambda cls: SimpleNamespace(find_one=find_one)))
    item = Document(title="Coffee", description="", price=50, creator="alice", min_level=1)
    player = user(Spoints=100, sale_shop=0.985)
    balance = BalanceCollection(100)
    monkeypatch.setattr(user_service.repository.model, "get_pymongo_collection", lambda: balance)
    monkeypatch.setattr(item_service.shop_items_repo, "get", AsyncMock(return_value=item))
    monkeypatch.setattr(item_service.user_repo, "get_by_name", AsyncMock(return_value=player))
    if saved:
        result = await item_service.buy_item("item-id", "alice")
        assert result["title"] == "Coffee"
        assert state["document"]["price"] == 49.25
    else:
        with pytest.raises(PurchaseStatusUnknownError):
            await item_service.buy_item("item-id", "alice")
    assert balance.balance == 50.75
