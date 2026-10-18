from authx import AuthX, AuthXConfig
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException

from models.models import User
from models.settings import settings
from repositories import user_repo


config = AuthXConfig(
    JWT_SECRET_KEY=settings.jwt_secret,
    JWT_ALGORITHM="HS256",
    JWT_TOKEN_LOCATION=["headers"],
)


async def get_user_from_uid(uid: str) -> dict:
    """Load a user through the shared async repository, preserving the handler data format."""
    try:
        user = await user_repo.get_by_name(uid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user.model_dump(by_alias=True)


class UserAuth(AuthX):
    """Resolve authenticated users asynchronously without AuthX's synchronous callback."""

    async def get_current_subject(self, request: Request) -> dict:
        token = await self.access_token_required(request)
        return await get_user_from_uid(token.sub)


security = UserAuth(
    config=config,
    model=User,
)


def load_security_handle_errors(app: FastAPI):
    """Register AuthX error responses for the application."""
    security.handle_errors(app)
