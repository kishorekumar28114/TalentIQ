"""LangGraph Agent state definition."""

from typing import List, Dict, Any, Optional
from langgraph.graph import MessagesState


class JobAgentState(MessagesState):
    """Extended agent state with conversational metadata."""
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    tools_called: Optional[List[str]] = None
