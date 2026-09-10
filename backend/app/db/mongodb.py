"""Async MongoDB client connection management using Motor and PyMongo."""

import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from app.core.config import settings
from app.core.logging import logger


class MongoDBManager:
    """Manages Async Motor and Synchronous PyMongo connections."""

    def __init__(self):
        self.motor_client: Optional[AsyncIOMotorClient] = None
        self.pymongo_client: Optional[MongoClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.is_connected: bool = False

    async def connect(self):
        """Initializes database connections with graceful connectivity check."""
        try:
            # Mask password for safe logging
            masked_uri = settings.MONGODB_URI
            if "@" in masked_uri and "://" in masked_uri:
                prefix, rest = masked_uri.split("://", 1)
                user_pass, host = rest.split("@", 1)
                masked_uri = f"{prefix}://*****:*****@{host}"

            logger.info("Connecting to MongoDB at %s...", masked_uri)
            
            # Motor Async Client
            self.motor_client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Verify connectivity with server_info
            await self.motor_client.server_info()
            self.db = self.motor_client[settings.MONGODB_DB_NAME]

            # Synchronous client for LangGraph checkpointer
            self.pymongo_client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.is_connected = True
            logger.info("Successfully connected to MongoDB database '%s'.", settings.MONGODB_DB_NAME)

            # Ensure indexes on users collection
            try:
                await self.db["users"].create_index("email", unique=True)
            except Exception as idx_err:
                logger.debug("Users email index creation notice: %s", idx_err)
        except Exception as e:
            self.is_connected = False
            logger.warning(
                "MongoDB connection unavailable (%s). "
                "The backend will continue in in-memory fallback mode for local sessions.",
                str(e)
            )

    async def disconnect(self):
        """Closes active MongoDB connections."""
        if self.motor_client:
            self.motor_client.close()
            logger.info("Closed Motor MongoDB connection.")
        if self.pymongo_client:
            self.pymongo_client.close()
            logger.info("Closed PyMongo connection.")
        self.is_connected = False

    def get_collection(self, collection_name: str):
        """Returns the requested Motor collection or None if disconnected."""
        if self.is_connected and self.db is not None:
            return self.db[collection_name]
        return None

    # --- USER & RESUME MAPPING OPERATIONS ---

    async def create_user(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new user record in MongoDB with unique email constraint."""
        import uuid
        from datetime import datetime, timezone
        from bson import ObjectId

        user_copy = dict(user_doc)
        user_copy.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        user_copy.setdefault("resume", None)

        coll = self.get_collection("users")
        if coll is not None:
            res = await coll.insert_one(user_copy)
            user_copy["_id"] = str(res.inserted_id)
            user_copy["id"] = str(res.inserted_id)
            return user_copy

        # Fallback local in-memory storage
        if not hasattr(self, "_memory_users"):
            self._memory_users = {}
        
        user_id = str(ObjectId()) if ObjectId else uuid.uuid4().hex[:24]
        user_copy["_id"] = user_id
        user_copy["id"] = user_id
        self._memory_users[user_id] = user_copy
        logger.info("Stored user '%s' in memory session cache (id: %s).", user_copy.get("email"), user_id)
        return user_copy

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by normalized email."""
        from bson import ObjectId

        normalized_email = email.lower().strip()
        coll = self.get_collection("users")
        if coll is not None:
            doc = await coll.find_one({"email": normalized_email})
            if doc:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
                return doc
            return None

        # Fallback memory search
        if not hasattr(self, "_memory_users"):
            self._memory_users = {}
        for u in self._memory_users.values():
            if u.get("email", "").lower().strip() == normalized_email:
                return u
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by MongoDB ObjectId or string id."""
        from bson import ObjectId

        coll = self.get_collection("users")
        if coll is not None:
            doc = None
            try:
                doc = await coll.find_one({"_id": ObjectId(user_id)})
            except Exception:
                pass
            if not doc:
                doc = await coll.find_one({"_id": user_id})
            if doc:
                doc["id"] = str(doc["_id"])
                doc["_id"] = str(doc["_id"])
                return doc
            return None

        # Fallback memory search
        if not hasattr(self, "_memory_users"):
            self._memory_users = {}
        return self._memory_users.get(user_id)

    async def update_user_resume(self, user_id: str, resume_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Maps Cloudinary resume details, parsed profile, and fits to the user's MongoDB record."""
        from bson import ObjectId
        from datetime import datetime, timezone

        resume_payload = dict(resume_data)
        resume_payload.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())

        coll = self.get_collection("users")
        if coll is not None:
            filter_query = None
            try:
                filter_query = {"_id": ObjectId(user_id)}
            except Exception:
                filter_query = {"_id": user_id}

            await coll.update_one(filter_query, {"$set": {"resume": resume_payload}})
            return await self.get_user_by_id(user_id)

        # Fallback memory update
        if not hasattr(self, "_memory_users"):
            self._memory_users = {}
        if user_id in self._memory_users:
            self._memory_users[user_id]["resume"] = resume_payload
            logger.info("Updated Cloudinary resume mapping for user '%s'.", user_id)
            return self._memory_users[user_id]
        return None

    async def remove_user_resume(self, user_id: str) -> bool:
        """Removes the mapped resume from user profile."""
        from bson import ObjectId

        coll = self.get_collection("users")
        if coll is not None:
            try:
                filter_query = {"_id": ObjectId(user_id)}
            except Exception:
                filter_query = {"_id": user_id}
            await coll.update_one(filter_query, {"$set": {"resume": None}})
            return True

        if hasattr(self, "_memory_users") and user_id in self._memory_users:
            self._memory_users[user_id]["resume"] = None
            return True
        return False

    async def save_resume_record(self, record: Dict[str, Any]) -> str:
        """Stores a parsed resume and matchmaking outcome."""
        coll = self.get_collection("resumes")
        if coll is not None:
            res = await coll.insert_one(record)
            return str(res.inserted_id)
        return "local_memory_id"

    async def get_resume_history(self, limit: int = 20):
        """Retrieves recent resume parsing and matchmaking history."""
        coll = self.get_collection("resumes")
        if coll is not None:
            cursor = coll.find({}).sort("_id", -1).limit(limit)
            items = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                items.append(doc)
            return items
        return []


mongo_manager = MongoDBManager()
