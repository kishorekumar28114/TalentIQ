"""Schemas for conversational LangGraph agent interface."""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Input payload for POST /api/chat."""
    message: str = Field(..., description="User query or message to the agent")
    thread_id: Optional[str] = Field(
        default=None,
        description="Session thread ID for MongoDB state checkpointer memory. If omitted, a new thread ID is created."
    )
    user_id: Optional[str] = Field(default=None, description="Optional user or candidate identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra profile or job match context")


class ToolExecutionRecord(BaseModel):
    """Details of tools invoked during the agent's turn."""
    tool_name: str
    query: str
    results_count: int


class ChatResponse(BaseModel):
    """Response returned by POST /api/chat."""
    success: bool = True
    response: str
    thread_id: str
    tools_used: List[str] = Field(default_factory=list, description="Names of tools called by the agent (e.g. ChromaDB, WebSearchTool)")
    citations: List[Dict[str, str]] = Field(default_factory=list, description="Extracted URLs or company references")
