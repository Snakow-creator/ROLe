from pymongo import MongoClient
from models.settings import settings

# init database
client = MongoClient(settings.mongo_address, port=27017)
role_db = client["role_db"]

# init collections
users = role_db["users"]
levels = role_db["levels"]
shop_items = role_db["shop_items"]
tasks = role_db["tasks"]
items = role_db["items"]
users_avatars = role_db["users_avatars"]
boards = role_db["boards"]
