"""API v1 Router aggregation."""

from fastapi import APIRouter
from app.api.api_v1.endpoints import health, data, match, chat, auth

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication & User Management"])
api_router.include_router(data.router, tags=["Data Ingestion & Live Scraping"])
api_router.include_router(match.router, tags=["Resume Processing & Matchmaking"])
api_router.include_router(chat.router, tags=["Conversational Agent (LangGraph)"])
