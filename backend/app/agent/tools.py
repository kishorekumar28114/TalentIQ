"""Tools for LangGraph Stateful Agent: ChromaDB Search and DuckDuckGo Web Search."""

from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from app.core.logging import logger
from app.db.chroma import chroma_manager

# Import DDGS
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


@tool
def search_job_market_database(query: str, company: Optional[str] = None) -> str:
    """Search internal ChromaDB 'job_market' database for companies, open roles, skills, and tech stacks.

    Args:
        query: The search keywords, role title, or skill description (e.g. 'Backend Engineer Python', 'Distributed Systems').
        company: Optional company name to filter or search for (e.g. 'Google', 'Meta', 'Netflix').

    Returns:
        String containing matched company jobs, tech stacks, or explicit notice if the company is not in the database.
    """
    logger.info("Tool invoked: search_job_market_database(query='%s', company='%s')", query, company)

    # If specific company queried, also check direct company metadata
    search_text = f"{company} {query}" if company else query
    results = chroma_manager.query_jobs(query_text=search_text, n_results=4)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    # Check if results are empty or if requested company is not present
    if not documents:
        target_name = company or query
        return (
            f"NOTICE: Company or role '{target_name}' is NOT present in the internal ChromaDB job_market database. "
            f"You MUST autonomously use the 'search_web_for_jobs' tool now to find live job openings and tech stack info on the internet."
        )

    # Check if company filter was provided and if any of the matched documents actually mention that company
    if company:
        company_matches = [
            (doc, meta) for doc, meta in zip(documents, metadatas)
            if company.lower() in meta.get("company", "").lower() or company.lower() in doc.lower()
        ]
        if not company_matches:
            return (
                f"NOTICE: Company '{company}' is NOT present in the internal ChromaDB context. "
                f"The database only returned unrelated general jobs. "
                f"You MUST autonomously use the 'search_web_for_jobs' tool to find live job openings and engineering details for '{company}' on the internet."
            )
        documents = [m[0] for m in company_matches]
        metadatas = [m[1] for m in company_matches]

    formatted_docs = []
    for idx, (doc, meta) in enumerate(zip(documents, metadatas)):
        source_type = meta.get("source", "unknown")
        comp = meta.get("company", "Tech Company")
        title = meta.get("title", "Role")
        url = meta.get("url", "")
        formatted_docs.append(
            f"[{idx + 1}] Company: {comp} | Role: {title} | Source: {source_type}\n"
            f"URL: {url}\n"
            f"Content:\n{doc}\n"
        )

    return (
        f"Found {len(formatted_docs)} internal record(s) in ChromaDB:\n\n"
        + "\n---\n".join(formatted_docs)
    )


@tool
def search_web_for_jobs(company: str, role_or_skill: Optional[str] = "software engineer") -> str:
    """Search the live internet using DuckDuckGo for live job openings, tech stack details, and engineering blogs.

    Use this tool whenever a company or role is NOT found in ChromaDB, or when the user specifically requests live web data.

    Args:
        company: The target company name (e.g. 'Anthropic', 'Palantir', 'Figma', 'Stripe').
        role_or_skill: Role, skill, or department to look for (e.g. 'Backend Engineer', 'AI Platform', 'Full Stack').

    Returns:
        Live search snippets, job posting links, and architectural notes retrieved from the web.
    """
    logger.info("Tool invoked: search_web_for_jobs(company='%s', role_or_skill='%s')", company, role_or_skill)

    if DDGS is None:
        return f"Live web search engine is unavailable. Unable to search for {company}."

    search_query = f"{company} {role_or_skill} careers hiring jobs tech stack 2025 2026"
    results_snippets = []

    try:
        with DDGS() as ddgs:
            # Query job openings
            for r in ddgs.text(search_query, max_results=4):
                results_snippets.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })

            # Also query tech stack
            tech_query = f"{company} engineering tech stack architecture blog"
            for r in ddgs.text(tech_query, max_results=2):
                results_snippets.append({
                    "title": f"[Tech Stack] {r.get('title', '')}",
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })

    except Exception as e:
        logger.error("WebSearchTool error for %s: %s", company, e)
        return f"Error executing DuckDuckGo search for '{company}': {str(e)}"

    if not results_snippets:
        return f"No live web results found for company '{company}' on DuckDuckGo."

    formatted_results = []
    for idx, item in enumerate(results_snippets):
        formatted_results.append(
            f"[{idx + 1}] Title: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"Snippet: {item['snippet']}\n"
        )

    return (
        f"Live Web Search Results for '{company}' ({role_or_skill}):\n\n"
        + "\n---\n".join(formatted_results)
    )
