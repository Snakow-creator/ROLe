import mongomock
import pytest

from models.models import Board, Task, User


class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.cursor)
        except StopIteration:
            raise StopAsyncIteration

    async def to_list(self, length=None):
        return list(self.cursor)


class Collection:
    def __init__(self, collection):
        self.raw = collection
        self.fail_cleanup_once = False

    def find(self, query):
        return Cursor(self.raw.find(query))

    async def aggregate(self, pipeline):
        return Cursor(self.raw.aggregate(pipeline))

    async def update_many(self, query, update):
        return self.raw.update_many(query, update)

    async def update_one(self, query, update):
        if self.fail_cleanup_once and "$unset" in update:
            self.fail_cleanup_once = False
            raise RuntimeError("Simulated interruption before user cleanup")
        return self.raw.update_one(query, update)

    async def count_documents(self, query):
        return self.raw.count_documents(query)


class Field:
    def __init__(self, name):
        self.name = name

    def __eq__(self, value):
        return {self.name: value}


@pytest.fixture
def database(monkeypatch):
    db = mongomock.MongoClient().role_migration_test
    collections = {name: Collection(db[name]) for name in ("boards", "tasks", "users")}
    for model, name in [(Board, "boards"), (Task, "tasks"), (User, "users")]:
        collection = collections[name]
        monkeypatch.setattr(model, "get_pymongo_collection", classmethod(lambda cls, c=collection: c))
    monkeypatch.setattr(Board, "username", Field("username"), raising=False)
    monkeypatch.setattr(Board, "title", Field("title"), raising=False)

    async def find_one(cls, *conditions):
        document = db.boards.find_one({"$and": list(conditions)})
        return cls.model_validate(document) if document else None

    async def insert(self):
        document = self.model_dump(by_alias=True)
        document.pop("_id", None)
        self.id = db.boards.insert_one(document).inserted_id
        return self

    monkeypatch.setattr(Board, "find_one", classmethod(find_one))
    monkeypatch.setattr(Board, "insert", insert)
    return db, collections
