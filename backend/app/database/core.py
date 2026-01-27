from pymongo import MongoClient
from models.settings import settings

# init database
client = MongoClient(settings.mongo_address, port=27017)
role_db = client[settings.collection_name]

# init collections
users = role_db["users"]
levels = role_db["levels"]
shop_items = role_db["shop_items"]
baseTasks = role_db["baseTasks"]
tasks = role_db["tasks"]
