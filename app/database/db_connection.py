from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config.settings import settings
from app.utils.logger import logger

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:  # pragma: no cover - optional dependency during local planning
    AsyncIOMotorClient = None

try:
    import certifi
except Exception:  # pragma: no cover - optional dependency during local planning
    certifi = None


class CollectionResult:
    def __init__(self, inserted_id: str | None = None, modified_count: int = 0, deleted_count: int = 0):
        self.inserted_id = inserted_id
        self.modified_count = modified_count
        self.deleted_count = deleted_count


class InMemoryCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return deepcopy(document)
        return None

    async def insert_one(self, document: dict[str, Any]) -> CollectionResult:
        self.documents.append(deepcopy(document))
        return CollectionResult(inserted_id=document.get("id"))

    async def replace_one(self, query: dict[str, Any], document: dict[str, Any]) -> CollectionResult:
        for index, current in enumerate(self.documents):
            if all(current.get(key) == value for key, value in query.items()):
                self.documents[index] = deepcopy(document)
                return CollectionResult(modified_count=1)
        return CollectionResult()

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> CollectionResult:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                for key, value in update.get("$set", {}).items():
                    document[key] = deepcopy(value)
                return CollectionResult(modified_count=1)
        return CollectionResult()

    async def delete_one(self, query: dict[str, Any]) -> CollectionResult:
        for index, document in enumerate(self.documents):
            if all(document.get(key) == value for key, value in query.items()):
                self.documents.pop(index)
                return CollectionResult(deleted_count=1)
        return CollectionResult()

    async def delete_many(self, query: dict[str, Any]) -> CollectionResult:
        kept: list[dict[str, Any]] = []
        deleted = 0
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                deleted += 1
            else:
                kept.append(document)
        self.documents = kept
        return CollectionResult(deleted_count=deleted)

    async def find_many(
        self,
        query: dict[str, Any] | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        query = query or {}
        results = [deepcopy(document) for document in self.documents if all(document.get(key) == value for key, value in query.items())]
        if sort:
            for field, direction in reversed(sort):
                results.sort(key=lambda item: item.get(field), reverse=direction < 0)
        if skip:
            results = results[skip:]
        if limit:
            results = results[:limit]
        return results

    async def count_documents(self, query: dict[str, Any] | None = None) -> int:
        return len(await self.find_many(query))

    async def create_index(self, *args: Any, **kwargs: Any) -> None:
        return None


class InMemoryDatabase:
    def __init__(self) -> None:
        self.users = InMemoryCollection()
        self.patients = InMemoryCollection()
        self.vitals = InMemoryCollection()
        self.labs = InMemoryCollection()
        self.predictions = InMemoryCollection()
        self.alerts = InMemoryCollection()
        self.system_settings = InMemoryCollection()
        self.audit_logs = InMemoryCollection()

    def collection(self, name: str) -> InMemoryCollection:
        return getattr(self, name)


class MotorCollectionAdapter:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        document = await self.collection.find_one(query, {"_id": 0})
        return deepcopy(document) if document else None

    async def insert_one(self, document: dict[str, Any]) -> Any:
        return await self.collection.insert_one(deepcopy(document))

    async def replace_one(self, query: dict[str, Any], document: dict[str, Any]) -> Any:
        return await self.collection.replace_one(query, deepcopy(document), upsert=False)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> Any:
        return await self.collection.update_one(query, update)

    async def delete_one(self, query: dict[str, Any]) -> Any:
        return await self.collection.delete_one(query)

    async def delete_many(self, query: dict[str, Any]) -> Any:
        return await self.collection.delete_many(query)

    async def find_many(
        self,
        query: dict[str, Any] | None = None,
        *,
        sort: list[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        cursor = self.collection.find(query or {}, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return [deepcopy(item) async for item in cursor]

    async def count_documents(self, query: dict[str, Any] | None = None) -> int:
        return await self.collection.count_documents(query or {})

    async def create_index(self, *args: Any, **kwargs: Any) -> Any:
        return await self.collection.create_index(*args, **kwargs)


class MotorDatabaseAdapter:
    def __init__(self, database: Any) -> None:
        self.users = MotorCollectionAdapter(database["users"])
        self.patients = MotorCollectionAdapter(database["patients"])
        self.vitals = MotorCollectionAdapter(database["vitals"])
        self.labs = MotorCollectionAdapter(database["labs"])
        self.predictions = MotorCollectionAdapter(database["predictions"])
        self.alerts = MotorCollectionAdapter(database["alerts"])
        self.system_settings = MotorCollectionAdapter(database["system_settings"])
        self.audit_logs = MotorCollectionAdapter(database["audit_logs"])

    def collection(self, name: str) -> MotorCollectionAdapter:
        return getattr(self, name)


db_client: Any | None = None
db: MotorDatabaseAdapter | InMemoryDatabase = InMemoryDatabase()


async def _ensure_indexes(database: MotorDatabaseAdapter | InMemoryDatabase) -> None:
    await database.users.create_index("email", unique=True)
    await database.users.create_index("role")
    await database.patients.create_index("mrn", unique=True)
    await database.patients.create_index("ward")
    await database.vitals.create_index([("patient_id", 1), ("recorded_at", -1)])
    await database.labs.create_index([("patient_id", 1), ("collected_at", -1)])
    await database.predictions.create_index([("patient_id", 1), ("predicted_at", -1)])
    await database.alerts.create_index([("patient_id", 1), ("triggered_at", -1)])
    await database.alerts.create_index([("status", 1), ("severity", 1)])
    await database.system_settings.create_index("id", unique=True)
    await database.audit_logs.create_index([("timestamp", -1)])
    await database.audit_logs.create_index([("actor_role", 1), ("action", 1)])


async def init_db() -> None:
    global db_client, db
    if AsyncIOMotorClient is None:
        logger.warning("motor is unavailable; using in-memory database")
        db = InMemoryDatabase()
        await _ensure_indexes(db)
        return

    try:
        client_options: dict[str, Any] = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
            "socketTimeoutMS": 20000,
            "retryWrites": True,
        }
        if certifi is not None and settings.MONGODB_URL.startswith("mongodb+srv://"):
            client_options["tls"] = True
            client_options["tlsCAFile"] = certifi.where()

        db_client = AsyncIOMotorClient(settings.MONGODB_URL, **client_options)
        await db_client.admin.command("ping")
        db = MotorDatabaseAdapter(db_client[settings.MONGODB_DB_NAME])
        logger.info(f"MongoDB connected at {settings.MONGODB_URL}/{settings.MONGODB_DB_NAME}")
    except Exception as exc:  # pragma: no cover - depends on external infra
        logger.warning(f"MongoDB unavailable ({exc}); using in-memory database")
        db_client = None
        db = InMemoryDatabase()

    await _ensure_indexes(db)


async def close_db() -> None:
    global db_client
    if db_client is not None:
        db_client.close()
        db_client = None


async def get_db() -> MotorDatabaseAdapter | InMemoryDatabase:
    return db
