"""Health check and system diagnostics endpoint."""

from fastapi import APIRouter
from app.core.config import settings
from app.db.chroma import chroma_manager
from app.db.mongodb import mongo_manager
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health & Diagnostics")
async def health_check():
    """Returns the operational status of all backend subsystems:
    ChromaDB vector store, MongoDB client, Groq API, and Cloudinary.
    """
    total_records = chroma_manager.count()
    live_records = chroma_manager.count_by_source("live")
    excel_records = chroma_manager.count_by_source("excel")

    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        chromadb_connected=True,
        chromadb_total_records=total_records,
        chromadb_live_records=live_records,
        chromadb_excel_records=excel_records,
        mongodb_connected=mongo_manager.is_connected,
        groq_configured=settings.has_groq_key,
        groq_model=settings.GROQ_MODEL,
        cloudinary_configured=settings.has_cloudinary
    )
