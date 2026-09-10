"""Main FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.db.mongodb import mongo_manager
from app.db.chroma import chroma_manager
from app.api.api_v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager handling startup initialization and shutdown cleanup."""
    logger.info("=" * 60)
    logger.info(" Starting %s...", settings.PROJECT_NAME)
    logger.info("=" * 60)

    # 1. Initialize MongoDB connection
    await mongo_manager.connect()

    # 2. Seed permanent baseline Excel data if Chroma collection is unpopulated
    try:
        current_excel = chroma_manager.count_by_source("excel")
        if current_excel == 0:
            logger.info("Initializing baseline permanent 'excel' job dataset into ChromaDB...")
            chroma_manager.seed_excel_base_data()
        else:
            logger.info("ChromaDB already contains %d permanent 'excel' records.", current_excel)
    except Exception as e:
        logger.warning("Auto-seeding ChromaDB on startup encountered: %s", e)

    yield

    # Shutdown
    logger.info("Shutting down %s...", settings.PROJECT_NAME)
    await mongo_manager.disconnect()
    logger.info("Cleanup completed successfully.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production-Grade FastAPI Backend for an Agentic RAG Job Matchmaking Application.\n\n"
        "**Core Capabilities:**\n"
        "- **Two-Tier Vector DB Strategy**: ChromaDB 'job_market' collection with permanent 'excel' base data and dynamic 'live' data.\n"
        "- **Live Scraping Engine**: Real-time hiring and engineering tech stack scraper powered by DuckDuckGo (`ddgs`).\n"
        "- **Resume RAG Matchmaking**: PDF/Image parsing, Cloudinary hosting, Groq (Llama 3 70B) candidate profiling & fit synthesis.\n"
        "- **Conversational Agent**: Stateful LangGraph agent backed by MongoDB checkpointer memory and autonomous web search fallback."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount uploads directory for resume document preview and fallback serving
import os
from fastapi.staticfiles import StaticFiles

uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint welcoming clients and directing to OpenAPI documentation."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "endpoints": {
            "trigger_live_scraping": f"{settings.API_V1_STR}/data/trigger-live",
            "scrape_portal": f"{settings.API_V1_STR}/data/scrape-portal",
            "seed_base_data": f"{settings.API_V1_STR}/data/seed-base",
            "match_resume": f"{settings.API_V1_STR}/match/resume",
            "chat_agent": f"{settings.API_V1_STR}/chat"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception safety net."""
    logger.exception("Unhandled server error processing request to %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
