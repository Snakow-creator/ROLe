from pymongo import AsyncMongoClient

from models.settings import settings
from models.models import *

import beanie


async def drop_tests_collection():
    await User.delete_all()


async def init_db():
    client = AsyncMongoClient(settings.mongo_url)
    collection = settings.collection_name
    await beanie.init_beanie(
        database=client[collection],
        document_models=[User, Level, ShopItem, Task, Item, UsersAvatars, Board],
    )

