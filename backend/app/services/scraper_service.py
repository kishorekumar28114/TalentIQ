"""Live Scraping Engine using DuckDuckGo (ddgs).

Workflow:
  1. Delete all existing ChromaDB records where metadata={"source": "live"}.
  2. Iterate through a static list of companies, scrape live jobs and tech stack blogs.
  3. Generate embeddings and insert into ChromaDB with metadata={"source": "live"}.
"""

import time
import asyncio
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.db.chroma import chroma_manager
from app.schemas.data import TriggerLiveResponse, CompanyScrapeDetail
from app.services.job_company_scraper import job_company_scraper

# Import DDGS with safe fallback
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


class LiveScraperService:
    """Service to search live job postings and tech stack blogs via DuckDuckGo."""

    def __init__(self):
        self.companies: List[str] = list(settings.TARGET_COMPANIES)

    def scrape_company_sync(self, company: str, max_results: int = 3) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Synchronously searches DDGS for jobs and tech stack blogs for a specific company."""
        if DDGS is None:
            logger.warning("DDGS library not available; returning empty scrape results.")
            return [], []

        job_results = []
        tech_results = []

        try:
            with DDGS() as ddgs:
                # 1. Search live job postings & careers
                job_query = f"{company} software engineer careers hiring jobs tech stack 2025 2026"
                try:
                    for r in ddgs.text(job_query, max_results=max_results):
                        job_results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")
                        })
                except Exception as e:
                    logger.warning("Error querying jobs for %s: %s", company, e)

                # Small delay to prevent rate limits
                time.sleep(0.5)

                # 2. Search engineering tech stack & architecture blogs
                tech_query = f"{company} engineering tech stack architecture system design blog"
                try:
                    for r in ddgs.text(tech_query, max_results=max_results):
                        tech_results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")
                        })
                except Exception as e:
                    logger.warning("Error querying tech stack for %s: %s", company, e)

        except Exception as e:
            logger.error("DDGS session failed for %s: %s", company, e)

        return job_results, tech_results

    async def scrape_company(self, company: str, max_results: int = 3) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Asynchronously wraps the synchronous DuckDuckGo search."""
        return await asyncio.to_thread(self.scrape_company_sync, company, max_results)

    async def trigger_live_workflow(self) -> TriggerLiveResponse:
        """Executes the full live data trigger workflow:

        1. Delete all existing ChromaDB records where metadata={"source": "live"}.
        2. Iterate through the static list of companies, scrape data using ddgs.
        3. Generate embeddings and insert into ChromaDB with metadata={"source": "live"}.
        """
        start_time = time.time()
        logger.info(">>> Starting Live Data Ingestion Workflow...")

        # STEP 1: Delete all existing ChromaDB records where metadata={"source": "live"}
        deleted_count = chroma_manager.delete_live_records()
        logger.info("Step 1 Complete: Purged %d previous 'live' records from ChromaDB.", deleted_count)

        # STEP 2 & 3: Iterate through companies, scrape via ddgs, and build documents
        details: List[CompanyScrapeDetail] = []
        all_documents: List[str] = []
        all_metadatas: List[Dict[str, Any]] = []

        total_new_records = 0

        for company in self.companies:
            logger.info("Scraping live data for company: %s...", company)
            try:
                job_posts, tech_blogs = await self.scrape_company(company, max_results=3)

                company_docs = 0
                # Process job postings
                for jp in job_posts:
                    if jp["snippet"]:
                        doc_text = (
                            f"Company: {company}\n"
                            f"Live Posting: {jp['title']}\n"
                            f"Details: {jp['snippet']}\n"
                            f"Careers URL: {jp['url']}"
                        )
                        all_documents.append(doc_text)
                        all_metadatas.append({
                            "source": "live",
                            "company": company,
                            "type": "job_posting",
                            "title": jp["title"],
                            "url": jp["url"],
                            "timestamp": int(time.time())
                        })
                        company_docs += 1

                # Process tech stack snippets
                for tb in tech_blogs:
                    if tb["snippet"]:
                        doc_text = (
                            f"Company: {company}\n"
                            f"Tech Stack / Engineering Insight: {tb['title']}\n"
                            f"Architecture & Systems: {tb['snippet']}\n"
                            f"Source URL: {tb['url']}"
                        )
                        all_documents.append(doc_text)
                        all_metadatas.append({
                            "source": "live",
                            "company": company,
                            "type": "tech_stack_blog",
                            "title": tb["title"],
                            "url": tb["url"],
                            "timestamp": int(time.time())
                        })
                        company_docs += 1

                total_new_records += company_docs
                details.append(CompanyScrapeDetail(
                    company=company,
                    job_postings_found=len(job_posts),
                    tech_stack_snippets_found=len(tech_blogs),
                    total_documents=company_docs,
                    status="SUCCESS" if company_docs > 0 else "NO_SNIPPETS"
                ))

            except Exception as e:
                logger.error("Failed scraping for company '%s': %s", company, e)
                details.append(CompanyScrapeDetail(
                    company=company,
                    job_postings_found=0,
                    tech_stack_snippets_found=0,
                    total_documents=0,
                    status=f"ERROR: {str(e)}"
                ))

        # STEP 3: Insert into ChromaDB with metadata={"source": "live"}
        if all_documents:
            logger.info("Inserting %d live documents into ChromaDB...", len(all_documents))
            chroma_manager.add_job_documents(
                documents=all_documents,
                metadatas=all_metadatas
            )
        else:
            logger.warning("No documents were scraped during DuckDuckGo trigger run.")

        # STEP 4: Scrape and Ingest Custom Job Portal (thejobcompany.co.in)
        portal_jobs_ingested = 0
        try:
            logger.info("Scraping custom portal https://thejobcompany.co.in/...")
            portal_jobs, portal_jobs_ingested = await job_company_scraper.scrape_and_ingest_live(max_jobs=15)
            total_new_records += portal_jobs_ingested
            details.append(CompanyScrapeDetail(
                company="TheJobCompany Portal (thejobcompany.co.in)",
                job_postings_found=len(portal_jobs),
                tech_stack_snippets_found=0,
                total_documents=portal_jobs_ingested,
                status="SUCCESS" if portal_jobs_ingested > 0 else "NO_JOBS"
            ))
            logger.info("Successfully ingested %d jobs from TheJobCompany portal.", portal_jobs_ingested)
        except Exception as portal_err:
            logger.error("Failed scraping TheJobCompany portal: %s", portal_err)
            details.append(CompanyScrapeDetail(
                company="TheJobCompany Portal (thejobcompany.co.in)",
                job_postings_found=0,
                tech_stack_snippets_found=0,
                total_documents=0,
                status=f"ERROR: {str(portal_err)}"
            ))

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            ">>> Live Ingestion Complete in %.2fs. Purged: %d, Ingested: %d records (DDG: %d, Portal: %d).",
            elapsed, deleted_count, total_new_records, total_new_records - portal_jobs_ingested, portal_jobs_ingested
        )

        return TriggerLiveResponse(
            success=True,
            message=f"Live scraping successfully completed for {len(self.companies)} companies and TheJobCompany portal.",
            deleted_previous_live_records=deleted_count,
            total_companies_processed=len(self.companies) + 1,
            total_new_records_ingested=total_new_records,
            portal_jobs_ingested=portal_jobs_ingested,
            elapsed_seconds=elapsed,
            details=details
        )


scraper_service = LiveScraperService()
