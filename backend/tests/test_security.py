from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.core.security import security
from models.models import User
from repositories import user_repo


@pytest.mark.asyncio
async def test_user_names_are_loaded_without_full_user_documents(database):
    db, _ = database
    db.users.insert_many([{"name": "alice"}, {"name": "bob"}])
    assert set(await user_repo.get_all_names()) == {"alice", "bob"}


@pytest.fixture
def subject_client():
    app = FastAPI()
    security.handle_errors(app)

    @app.get("/subject")
    async def subject(user=Depends(security.get_current_subject)):
        return {"name": user["name"], "level": user["level"]}

    with TestClient(app) as client:
        yield client


def test_valid_access_token_awaits_repository_and_preserves_user_dict(subject_client, monkeypatch):
    user = User.model_construct(name="alice", hashed_password="unused", level=3)
    lookup = AsyncMock(return_value=user)
    monkeypatch.setattr(user_repo, "get_by_name", lookup)
    token = security.create_access_token(uid="alice")

    response = subject_client.get("/subject", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"name": "alice", "level": 3}
    lookup.assert_awaited_once_with("alice")


@pytest.mark.parametrize("token_kind,expected_status", [
    ("missing", 401), ("invalid", 422), ("expired", 422), ("refresh", 401), ("revoked", 401),
])
def test_invalid_access_rejected_before_user_lookup(subject_client, monkeypatch, token_kind, expected_status):
    lookup = AsyncMock()
    monkeypatch.setattr(user_repo, "get_by_name", lookup)
    tokens = {
        "missing": None,
        "invalid": "invalid-token",
        "expired": security.create_access_token(uid="alice", expiry=timedelta(seconds=-1)),
        "refresh": security.create_refresh_token(uid="alice"),
        "revoked": security.create_access_token(uid="alice"),
    }
    if token_kind == "revoked":
        monkeypatch.setattr(security, "callback_is_token_in_blocklist", lambda token: True)
    token = tokens[token_kind]
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = subject_client.get("/subject", headers=headers)

    assert response.status_code == expected_status
    lookup.assert_not_awaited()


@pytest.mark.parametrize("database_error,expected_status,detail", [
    (False, 404, "User not found"),
    (True, 500, "Internal server error"),
])
def test_user_lookup_errors_preserve_http_responses(
    subject_client, monkeypatch, database_error, expected_status, detail,
):
    lookup = AsyncMock(return_value=None, side_effect=RuntimeError("database unavailable") if database_error else None)
    monkeypatch.setattr(user_repo, "get_by_name", lookup)
    token = security.create_access_token(uid="alice")

    response = subject_client.get("/subject", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == expected_status
    assert response.json() == {"detail": detail}
    lookup.assert_awaited_once_with("alice")
