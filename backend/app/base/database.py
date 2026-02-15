from motor.motor_asyncio import AsyncIOMotorClient

from models.settings import settings
from models.models import User, BaseTask, Level, ShopItem

import beanie


async def drop_tests_collection():
    await User.delete_all()


async def init_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    collection = settings.collection_name
    await beanie.init_beanie(
        database=client[collection],
        document_models=[User, Level, ShopItem, BaseTask],
    )

