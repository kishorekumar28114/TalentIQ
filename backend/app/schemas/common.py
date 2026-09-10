"""Common API schemas."""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class HealthResponse(BaseModel):
    """System health check schema."""
    status: str
    project: str
    chromadb_connected: bool
    chromadb_total_records: int
    chromadb_live_records: int
    chromadb_excel_records: int
    mongodb_connected: bool
    groq_configured: bool
    groq_model: str
    cloudinary_configured: bool
