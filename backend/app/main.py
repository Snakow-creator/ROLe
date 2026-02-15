from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

from models.models import User, Level, ShopItem, BaseTask, Task, Item, UsersAvatars
from models.settings import settings, baseSettings
from tasks import task_service
from base.database import drop_tests_collection
from users.requests import users_days_and_last_mul_expired
from api.core.security import load_security_handle_errors
from routers import init_router
from utils import load_data

import beanie
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def main(app: FastAPI):
    client = AsyncIOMotorClient(settings.mongo_url)
    collection = settings.collection_name
    # initialize db
    await beanie.init_beanie(
        database=client[collection],
        document_models=[User, Level, ShopItem, BaseTask, Task, Item, UsersAvatars],
    )
    # expire tasks and users data
    await task_service.update()
    await users_days_and_last_mul_expired()

    # init handle errors
    load_security_handle_errors(app)

    logging.info("ROLe is starting...")


    if collection == baseSettings.test_collection_name:
        await load_data()

    yield
    # end
    # if collection == baseSettings.test_collection_name:
    #     await drop_tests_collection()
    logging.info("ROLe is closing...")


origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://127.0.0.1:5173",
    "https://localhost:5173",
]

app = FastAPI(lifespan=main)
app.include_router(init_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # используем только проверенные адреса
    allow_credentials=True,  # отправка cookies, токенов, авторизационных заголовков
    allow_methods=["*"],  # использование всех методов(GET, POST, PUT, DELETE)
    allow_headers=["*"],  # любые headers
)

if __name__ == "__main__":
    settings.collection_name = baseSettings.collection_name
    uvicorn.run(app, host="127.0.0.1", port=7878)
