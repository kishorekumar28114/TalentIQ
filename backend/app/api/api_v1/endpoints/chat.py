"""Conversational Agent chat endpoint with LangGraph state and MongoDB checkpointer memory."""

import uuid
from fastapi import APIRouter, HTTPException, status
from app.core.logging import logger
from app.agent.graph import execute_agent_chat
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Stateful Job Matchmaking Agent (LangGraph + MongoDB Memory)"
)
async def chat_with_agent(request: ChatRequest):
    """Conversational endpoint backed by a stateful LangGraph agent:

    - **Stateful Memory**: Persists conversation history across turns using MongoDB checkpointer.
    - **Dual-Engine Retrieval**:
      1. First queries the internal ChromaDB `job_market` database for company details and verified roles.
      2. If the queried company or role is absent from ChromaDB, the agent **autonomously invokes the WebSearchTool** (`ddgs`) to scrape live internet openings and answers the user.
    """
    thread_id = request.thread_id or f"thread_{uuid.uuid4().hex[:12]}"
    logger.info("Chat request received for thread_id '%s': %s", thread_id, request.message[:80])

    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    try:
        chat_response = await execute_agent_chat(
            message=request.message,
            thread_id=thread_id,
            user_id=request.user_id,
            context=request.context
        )
        return chat_response
    except Exception as e:
        logger.error("Chat turn failed for thread '%s': %s", thread_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat agent encountered an error: {str(e)}"
        )
