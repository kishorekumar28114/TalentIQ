"""LangGraph Stateful Agent implementation with MongoDB checkpointer memory."""

import re
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from app.core.config import settings
from app.core.logging import logger
from app.agent.tools import search_job_market_database, search_web_for_jobs
from app.agent.checkpointer import checkpointer_factory
from app.schemas.chat import ChatResponse

AGENT_TOOLS = [search_job_market_database, search_web_for_jobs]

SYSTEM_PROMPT = """You are an elite Agentic Career Matchmaker & Technical Recruiter Assistant.
You possess deep knowledge of software engineering job markets, engineering architectures, and career pathways.

You have access to two tools:
1. `search_job_market_database`: Queries the internal ChromaDB database for verified company roles and tech stacks.
2. `search_web_for_jobs`: Live DuckDuckGo internet search engine for real-time hiring posts, active jobs, and engineering blogs.

STRICT OPERATIONAL PROTOCOL:
1. When the user asks about job openings, requirements, or tech stacks for a specific company or role:
   - FIRST search the internal database using `search_job_market_database`.
2. If `search_job_market_database` returns that the company or role is NOT present in the database (or only unrelated results):
   - You MUST AUTONOMOUSLY invoke `search_web_for_jobs` to search for live job openings and engineering details on the internet.
   - Never say "I don't know" or "We don't have that company" without running a live web search first.
3. Structure your final response with professional clarity:
   - State whether the findings came from internal database records or live web search.
   - Highlight key technical requirements (languages, cloud platforms, system design).
   - Provide clickable links where available.
"""


def get_llm():
    """Returns ChatGroq with bound tools, or None if key is missing."""
    if not settings.has_groq_key:
        return None

    try:
        llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.1
        )
        return llm.bind_tools(AGENT_TOOLS)
    except Exception as e:
        logger.warning("Error initializing ChatGroq with model %s: %s", settings.GROQ_MODEL, e)
        if settings.GROQ_MODEL != settings.GROQ_FALLBACK_MODEL:
            llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_FALLBACK_MODEL,
                temperature=0.1
            )
            return llm.bind_tools(AGENT_TOOLS)
        raise


def agent_node(state: MessagesState) -> Dict[str, Any]:
    """Node that invokes the Groq LLM with tools."""
    llm = get_llm()
    messages = state["messages"]

    # Prepend system prompt if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    if llm is None:
        # Fallback offline simulation when Groq API key is not configured
        user_msg = messages[-1].content if messages else ""
        return {"messages": [_simulate_agent_response(user_msg)]}

    try:
        response = llm.invoke(messages)
    except Exception as e:
        logger.warning("Agent invocation failed with model %s: %s. Attempting fallback model %s...", settings.GROQ_MODEL, e, settings.GROQ_FALLBACK_MODEL)
        try:
            fallback_llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_FALLBACK_MODEL,
                temperature=0.1
            ).bind_tools(AGENT_TOOLS)
            response = fallback_llm.invoke(messages)
        except Exception as e2:
            logger.error("Fallback LLM invocation also failed: %s. Returning fallback simulated response.", e2)
            user_msg = messages[-1].content if messages else ""
            return {"messages": [_simulate_agent_response(user_msg)]}

    return {"messages": [response]}


def _simulate_agent_response(user_message: str) -> AIMessage:
    """Provides a realistic simulation when Groq key is not configured."""
    logger.info("Executing simulated agent logic for offline testing...")
    # Extract company name from query if mentioned
    known_companies = ["google", "microsoft", "amazon", "meta", "apple", "netflix", "stripe", "uber", "databricks", "openai"]
    query_lower = user_message.lower()

    found_company = None
    for c in known_companies:
        if c in query_lower:
            found_company = c.title()
            break

    if found_company:
        tool_res = search_job_market_database.invoke({"query": user_message, "company": found_company})
        return AIMessage(content=(
            f"**[Internal Database Match]**\n\n"
            f"I checked our ChromaDB job market database for **{found_company}**:\n\n"
            f"{tool_res}\n\n"
            f"*(Note: Groq API key is currently not set; running in simulated local mode)*"
        ))
    else:
        # Company not known in base list -> autonomous web search simulation
        words = re.findall(r"\b[A-Z][a-z]+\b", user_message)
        potential_comp = words[0] if words else "Target Company"
        web_res = search_web_for_jobs.invoke({"company": potential_comp, "role_or_skill": "software engineer"})
        return AIMessage(content=(
            f"**[Live Web Search Result]**\n\n"
            f"Company **{potential_comp}** was not found in our ChromaDB internal database. "
            f"I autonomously searched DuckDuckGo for live job openings:\n\n"
            f"{web_res}\n\n"
            f"*(Note: Groq API key is currently not set; running in simulated local mode)*"
        ))


def build_job_agent_graph():
    """Builds and compiles the LangGraph stateful agent."""
    builder = StateGraph(MessagesState)

    # Nodes
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(AGENT_TOOLS))

    # Edges
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", END: END}
    )
    builder.add_edge("tools", "agent")

    # Compile with MongoDB checkpointer memory
    checkpointer = checkpointer_factory.get_checkpointer()
    graph = builder.compile(checkpointer=checkpointer)
    logger.info("Compiled LangGraph Job Matchmaking Agent with state checkpointer.")
    return graph


# Singleton graph instance
agent_graph = build_job_agent_graph()


async def execute_agent_chat(
    message: str,
    thread_id: str,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ChatResponse:
    """Executes a turn in the stateful LangGraph conversation.

    Preserves memory across turns via thread_id in the MongoDB checkpointer.
    """
    logger.info("Executing chat for thread_id '%s': %s", thread_id, message[:100])

    config = {"configurable": {"thread_id": thread_id}}
    input_messages = [HumanMessage(content=message)]

    tools_used = []
    final_content = ""

    try:
        # Stream or invoke the graph
        output_state = await agent_graph.ainvoke(
            {"messages": input_messages},
            config=config
        )

        all_messages = output_state.get("messages", [])

        # Extract tools called and final agent answer
        for msg in all_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name")
                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)

        if all_messages:
            last_message = all_messages[-1]
            final_content = last_message.content if hasattr(last_message, "content") else str(last_message)

    except Exception as e:
        logger.error("Error executing agent graph: %s", e)
        # Graceful fallback response
        final_content = f"An error occurred while processing your request with the AI agent: {str(e)}"

    # Extract citations (URLs) from response
    citations = []
    urls = re.findall(r"https?://[^\s)\]]+", final_content)
    for u in set(urls):
        citations.append({"url": u, "type": "web_reference"})

    return ChatResponse(
        success=True,
        response=final_content,
        thread_id=thread_id,
        tools_used=tools_used,
        citations=citations
    )
