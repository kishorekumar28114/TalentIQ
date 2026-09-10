"""MongoDB Checkpointer for LangGraph Stateful Memory."""

from typing import Optional
from pymongo import MongoClient
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from app.core.config import settings
from app.core.logging import logger
from app.db.mongodb import mongo_manager

try:
    from langgraph.checkpoint.mongodb import MongoDBSaver
except ImportError:
    MongoDBSaver = None


class CheckpointerFactory:
    """Manages creation and retrieval of the LangGraph checkpointer."""

    def __init__(self):
        self._memory_saver = MemorySaver()

    def get_checkpointer(self) -> BaseCheckpointSaver:
        """Returns MongoDB Checkpointer if connected, or InMemorySaver as fallback."""
        if mongo_manager.is_connected and mongo_manager.pymongo_client is not None and MongoDBSaver is not None:
            try:
                saver = MongoDBSaver(
                    client=mongo_manager.pymongo_client,
                    db_name=settings.MONGODB_DB_NAME,
                    checkpoint_collection_name="agent_checkpoints",
                    writes_collection_name="agent_checkpoint_writes"
                )
                logger.debug("Using MongoDBSaver for conversation state checkpointing.")
                return saver
            except Exception as e:
                logger.warning("Failed to initialize MongoDBSaver: %s. Using MemorySaver fallback.", e)

        logger.debug("Using MemorySaver for conversation state.")
        return self._memory_saver


checkpointer_factory = CheckpointerFactory()
