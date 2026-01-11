from pydantic import BaseModel
from authx import AuthX, AuthXConfig
from fastapi import FastAPI

from models.models import User
from models.settings import settings
from database.core import role_db


users = role_db["users"]

config = AuthXConfig(
    JWT_SECRET_KEY=settings.jwt_secret,
    JWT_ALGORITHM="HS256",
    JWT_TOKEN_LOCATION=["headers"],
)

security = AuthX(
    config=config,
    model=User,
)

# handler errors, init fastapi
def load_security_handle_errors(app: FastAPI):
    security.handle_errors(app)


# create query in mongodb
@security.set_subject_getter
def get_user_from_uid(uid: str) -> User:
    user = users.find_one({"name": uid})
    return user
