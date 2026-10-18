from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager

from models.models import *
from models.settings import settings
from tasks import task_service
from tasks.scheduler import task_update_scheduler

from users import user_service
from api.core.security import load_security_handle_errors
from migrations.boards import migrate_tasks_to_boards
from routers import init_router
from base.utils import load_data

import beanie
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def main(app: FastAPI):
    client = AsyncMongoClient(settings.mongo_url)
    try:
        collection = settings.collection_name
        await beanie.init_beanie(
            database=client[collection],
            document_models=[User, Level, ShopItem, Task, Item, UsersAvatars, Board, PlanEntry, PlanTemplate],
        )

        await migrate_tasks_to_boards()
        await task_service.update()
        await user_service.refresh_expired_bonuses()
        load_security_handle_errors(app)

        await load_data()

        async with task_update_scheduler():
            logging.info("ROLe is starting...")
            yield
    finally:
        # The scheduler exits before its database connection is closed.
        await client.close()
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
    uvicorn.run(app, host="127.0.0.1", port=8111)
