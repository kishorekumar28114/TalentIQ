from fastapi import APIRouter, HTTPException, status
import time
from app.core.logging import logger
from app.db.chroma import chroma_manager
from app.services.scraper_service import scraper_service
from app.services.job_company_scraper import job_company_scraper
from app.schemas.data import TriggerLiveResponse, SeedDataResponse, PortalScrapeResponse, PortalJobItem

router = APIRouter()


@router.post(
    "/data/scrape-portal",
    response_model=PortalScrapeResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape TheJobCompany Portal and Embed into ChromaDB"
)
async def scrape_job_company_portal(max_jobs: int = 15):
    """Scrapes the custom job portal `https://thejobcompany.co.in/`:
    
    1. Extracts job listings with Experience required, Passing out year, JD, and direct Apply link.
    2. Embeds the documents into ChromaDB under metadata `source='live'` and `portal='thejobcompany'`.
    """
    logger.info("Received request to scrape custom job portal (max_jobs=%d).", max_jobs)
    start_time = time.time()
    try:
        jobs, embedded_count = await job_company_scraper.scrape_and_ingest_live(max_jobs=max_jobs)
        elapsed = round(time.time() - start_time, 2)
        
        parsed_items = [
            PortalJobItem(
                title=j.get("title", ""),
                company=j.get("company", ""),
                experience_required=j.get("experience_required", ""),
                passing_out_year=j.get("passing_out_year", ""),
                job_description=j.get("job_description", ""),
                apply_link=j.get("apply_link", ""),
                location=j.get("location"),
                salary=j.get("salary")
            )
            for j in jobs
        ]
        
        return PortalScrapeResponse(
            success=True,
            message=f"Successfully scraped {len(jobs)} jobs from thejobcompany.co.in and embedded {embedded_count} records into ChromaDB.",
            jobs_scraped=len(jobs),
            jobs_embedded=embedded_count,
            elapsed_seconds=elapsed,
            jobs=parsed_items
        )
    except Exception as e:
        logger.error("Failed to scrape portal: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portal scraping failed: {str(e)}"
        )


@router.post(
    "/data/trigger-live",
    response_model=TriggerLiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Live Scraping & Vector DB Ingestion"
)
async def trigger_live_scraping():
    """Executes the live scraping pipeline:

    1. Deletes all existing ChromaDB records where `metadata={"source": "live"}`.
    2. Iterates through the predefined static list of companies and scrapes job postings and tech stack blogs using DuckDuckGo (`ddgs`).
    3. Scrapes `thejobcompany.co.in` for real-time parsed jobs (Experience, Batch, JD, Apply Link).
    4. Generates embeddings and inserts all fresh records into ChromaDB with `metadata={"source": "live"}`.
    """
    logger.info("Received request to trigger live scraping pipeline.")
    try:
        response = await scraper_service.trigger_live_workflow()
        return response
    except Exception as e:
        logger.error("Failed to execute live scraping workflow: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Live scraping workflow encountered an error: {str(e)}"
        )


@router.post(
    "/data/seed-base",
    response_model=SeedDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Seed Base Permanent Excel Data into ChromaDB"
)
async def seed_base_data(force: bool = False):
    """Populates the ChromaDB 'job_market' collection with permanent baseline jobs (`source: 'excel'`)
    as the reliable fallback dataset.
    """
    logger.info("Received request to seed baseline Excel data (force=%s).", force)
    try:
        seeded_count = chroma_manager.seed_excel_base_data(force=force)
        total_excel = chroma_manager.count_by_source("excel")
        return SeedDataResponse(
            success=True,
            message=f"Seeded {seeded_count} base records. Total permanent Excel records in ChromaDB: {total_excel}.",
            total_excel_records=total_excel
        )
    except Exception as e:
        logger.error("Failed to seed base Excel data: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed base data failed: {str(e)}"
        )
