from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from base.task_timing import TASK_TIMEZONE
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
