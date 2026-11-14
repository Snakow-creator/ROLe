from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.core.security import security
from base.task_timing import TASK_TIMEZONE
from models.models import User
from repositories import board_repo, user_repo
from routers import init_router
from users import user_service, weekly_bonus
from test_gameplay import user


NOW = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)


@pytest.mark.asyncio
@pytest.mark.parametrize("date_format", ["naive", "aware", "iso"])
async def test_expired_bonuses_support_existing_date_formats(monkeypatch, date_format):
    def stored(value):
        if date_format == "naive":
            return value.replace(tzinfo=None)
        if date_format == "iso":
            return value.isoformat()
        return value.astimezone(TASK_TIMEZONE)

    player = user(
        days_streak=5, mul=1.5, sale_shop=0.8,
        last_streak=stored(NOW - timedelta(days=1)),
        last_mul=stored(NOW - timedelta(days=14)),
    )
    monkeypatch.setattr(user_service.repository, "find_all", AsyncMock(return_value=[player]))
    await user_service.refresh_expired_bonuses(NOW)
    assert (player.days_streak, player.mul, player.sale_shop) == (1, 1, 1)


@pytest.mark.asyncio
async def test_recent_bonuses_are_not_updated(monkeypatch):
    player = user(last_streak=NOW - timedelta(hours=23), last_mul=NOW - timedelta(days=13), mul=1.5)
    player.update = AsyncMock()
    monkeypatch.setattr(user_service.repository, "find_all", AsyncMock(return_value=[player]))
    await user_service.refresh_expired_bonuses(NOW)
    player.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_multiple_level_rewards_are_reversible_without_reloading_the_user(monkeypatch):
    player = user(Spoints=10)
    lookup = AsyncMock()
    monkeypatch.setattr(user_service.repository, "get_by_name", lookup)
    assert (await user_service.set_level(player, 4))["points"] == 600
    assert (player.level, player.Spoints) == (4, 610)
    assert (await user_service.set_level(player, 1))["points"] == 600
    assert (player.level, player.Spoints) == (1, 10)
    lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_weekly_bonus_restores_previous_settings():
    player = user(Spoints=50, xp=20, mul=1.5, sale_shop=0.8, last_mul=NOW)
    claimed = await weekly_bonus.claim(player)
    assert (player.Spoints, player.xp) == (200, 170)
    assert player.mul == pytest.approx(1.53)
    assert player.sale_shop == pytest.approx(0.788)
    assert claimed.type == "claim_weekly_bonus"
    revoked = await weekly_bonus.revoke(player)
    assert (player.Spoints, player.xp, player.mul, player.sale_shop, player.last_mul) == (50, 20, 1.5, 0.8, NOW)
    assert revoked.type == "revoke_weekly_bonus"


@pytest.mark.asyncio
async def test_login_data_serializes_legacy_dates_in_utc(monkeypatch):
    player = user(last_streak=NOW.isoformat(), last_mul=NOW.replace(tzinfo=None))
    monkeypatch.setattr(user_service.repository, "get_by_name", AsyncMock(return_value=player))
    result = await user_service.load_data("alice")
    assert result["last_streak"] == result["last_mul"] == NOW.timestamp()
    assert result["name"] == "alice"


@pytest.mark.asyncio
async def test_role_avatar_grants_survive_undo_and_skip_repeated_roles():
    player = user()
    await user_service.change_rewards(player, 0, 1)
    await user_service.change_rewards(player, 0, 1, operation=-1)
    assert player.unlocked_avatar_ids == ["standart_avatar1_man", "standart_avatar1_woman"]

    await user_service.set_level(player, 2)
    await user_service.set_level(player, 5)  # Same role as level 2.
    assert len(player.unlocked_avatar_ids) == 4

    await user_service.set_level(player, 51)
    assert len(player.unlocked_avatar_ids) == 40
    assert player.unlocked_avatar_ids[-1] == "standart_avatar20_woman"


def test_avatar_selection_persists_only_available_catalog_entries(database, monkeypatch):
    db, _ = database
    db.users.insert_many([
        {"name": "alice", "hashed_password": "unused", "current_avatar": "avatar_default_1"},
        {"name": "bob", "hashed_password": "unused", "level": 6, "Qpoints": 17, "Spoints": 42.5, "Tpoints": 8},
    ])

    async def get_by_name(name):
        return User.model_validate(db.users.find_one({"name": name}))

    monkeypatch.setattr(user_repo, "get_by_name", get_by_name)
    monkeypatch.setattr(board_repo, "get_boards", AsyncMock(return_value=[]))
    app = FastAPI()
    app.include_router(init_router)
    security.handle_errors(app)
    alice_headers = {"Authorization": f"Bearer {security.create_access_token(uid='alice')}"}
    bob_headers = {"Authorization": f"Bearer {security.create_access_token(uid='bob')}"}

    with TestClient(app) as client:
        assert client.get("/profile").status_code == 401
        alice = client.get("/profile", headers=alice_headers).json()
        assert alice["avatar"] == "default_avatar_man"
        assert (alice["Qpoints"], alice["Spoints"], alice["Tpoints"]) == (0, 0, 0)
        assert len(alice["avatars"]) == 42
        assert [avatar["id"] for avatar in alice["avatars"] if avatar["available"]] == [
            "default_avatar_man", "default_avatar_woman",
        ]

        for unavailable in ("standart_avatar1_man", "standart_avatar20_woman", "custom_avatar"):
            response = client.put("/profile/avatar", headers=alice_headers, json={"avatar_id": unavailable})
            assert response.status_code == 403
        assert client.put("/profile/avatar", json={"avatar_id": "default_avatar_woman"}).status_code == 401
        assert db.users.find_one({"name": "alice"})["current_avatar"] == "avatar_default_1"

        response = client.put("/profile/avatar", headers=alice_headers, json={"avatar_id": "default_avatar_woman"})
        assert response.json() == {"avatar": "default_avatar_woman"}
        assert client.get("/profile/avatar", headers=alice_headers).status_code == 405
        assert client.get("/profile", headers=alice_headers).json()["avatar"] == "default_avatar_woman"

        response = client.put("/profile/avatar", headers=bob_headers, json={"avatar_id": "standart_avatar3_woman"})
        assert response.json() == {"avatar": "standart_avatar3_woman"}
        bob = client.get("/profile", headers=bob_headers).json()
        assert (bob["Qpoints"], bob["Spoints"], bob["Tpoints"]) == (17, 42.5, 8)
        assert db.users.find_one({"name": "alice"})["current_avatar"] == "default_avatar_woman"
