"""Schemas for live data ingestion and seed operations."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CompanyScrapeDetail(BaseModel):
    company: str
    job_postings_found: int
    tech_stack_snippets_found: int
    total_documents: int
    status: str


class PortalJobItem(BaseModel):
    """Parsed job listing extracted from thejobcompany.co.in portal."""
    title: str = Field(description="Role / Position title")
    company: str = Field(description="Hiring company name")
    experience_required: str = Field(description="Required experience level (e.g., Fresher, 0-1 Years, Experienced)")
    passing_out_year: str = Field(description="Target graduation batch / passing out year (e.g., 2027, 2026)")
    job_description: str = Field(description="Detailed job description and responsibilities")
    apply_link: str = Field(description="Direct external application link or portal apply URL")
    location: Optional[str] = Field(default=None, description="Job location")
    salary: Optional[str] = Field(default=None, description="Salary or stipend information")


class PortalScrapeResponse(BaseModel):
    """Response returned by POST /api/data/scrape-portal."""
    success: bool
    message: str
    jobs_scraped: int
    jobs_embedded: int
    elapsed_seconds: float
    jobs: List[PortalJobItem]


class TriggerLiveResponse(BaseModel):
    """Response returned by POST /api/data/trigger-live."""
    success: bool
    message: str
    deleted_previous_live_records: int
    total_companies_processed: int
    total_new_records_ingested: int
    portal_jobs_ingested: int = Field(default=0, description="Records ingested from thejobcompany.co.in portal")
    elapsed_seconds: float
    details: List[CompanyScrapeDetail]


class SeedDataResponse(BaseModel):
    """Response returned by POST /api/data/seed-base."""
    success: bool
    message: str
    total_excel_records: int
