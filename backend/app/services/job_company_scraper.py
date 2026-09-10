"""Custom Portal Scraper for https://thejobcompany.co.in/.

Workflow:
  1. Scrapes job listings from the target job portal.
  2. Extracts Experience required, Passing out year (Batch), Job Description (JD), and Apply Link.
  3. Formats documents and embeds them into ChromaDB under metadata source="live".
"""

import re
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from app.core.logging import logger
from app.db.chroma import chroma_manager
from app.schemas.data import PortalJobItem


class JobCompanyScraperService:
    """Dedicated scraping engine for thejobcompany.co.in portal."""

    BASE_URL = "https://thejobcompany.co.in/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _clean_text(self, text: Optional[str]) -> str:
        """Sanitizes extracted HTML text by normalizing whitespace."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def _parse_company_and_role(self, raw_title: str) -> Tuple[str, str]:
        """Parses 'Company is hiring Role' or 'Company - Role' into (company, role)."""
        raw_title = self._clean_text(raw_title)
        
        # Match 'Company is hiring Role'
        match = re.search(r"^(.*?)\s+is hiring\s+(.*)$", raw_title, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Match 'Company - Role'
        if " - " in raw_title:
            parts = raw_title.split(" - ", 1)
            return parts[0].strip(), parts[1].strip()

        # Fallback
        return "Tech Enterprise", raw_title

    def _derive_experience_required(
        self, batch_str: str, role_title: str, jd_text: str
    ) -> str:
        """Derives experience requirement from batch, role, and JD text."""
        combined = f"{batch_str} {role_title} {jd_text}".lower()

        # Explicit fresher / intern check
        if "intern" in role_title.lower() or "internship" in combined:
            return f"Fresher / Intern (Batch {batch_str})" if batch_str else "Fresher / Intern"
        if "fresher" in batch_str.lower() or "graduate engineer trainee" in combined:
            return "Fresher (0 Years)"

        # Search for explicit experience patterns (e.g., '2+ years', '0-2 yrs', '3 to 5 years')
        exp_match = re.search(
            r"(\d+\+?\s*(?:to|-)\s*\d+\+?\s*(?:years?|yrs?)|(?:\d+)\+?\s*(?:years?|yrs?))",
            combined,
            re.IGNORECASE
        )
        if exp_match:
            return exp_match.group(1).strip().capitalize()

        # Batch contains future / recent graduation years (e.g. 2025, 2026, 2027)
        year_matches = re.findall(r"\b(202[3-9]|2030)\b", batch_str)
        if year_matches:
            return f"Fresher / College Graduate (Batch {', '.join(year_matches)})"

        if "experience" in batch_str.lower() or "experienced" in batch_str.lower():
            return "1+ Years (Experienced)"

        return "Fresher / Entry-Level"

    def fetch_job_details(self, job_id: str, detail_url: str) -> Tuple[str, str, str]:
        """Fetches the detailed job description and direct apply link for a specific job_id.

        Returns:
            Tuple[job_description, apply_link, refined_experience]
        """
        job_description = ""
        apply_link = detail_url
        refined_exp = ""

        # 1. Fetch Job Details Page
        try:
            resp = self.session.get(detail_url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Extract text from detail container
                # Find elements describing job / responsibilities / qualifications
                content_blocks = []
                
                # Look for section headers or paragraphs
                for heading in soup.find_all(["h3", "h4", "strong"]):
                    h_text = heading.get_text(strip=True)
                    if any(k in h_text.lower() for k in ["about", "responsibilit", "qualification", "description", "eligibility", "role"]):
                        # Grab sibling or parent text
                        parent = heading.find_parent(["div", "section"])
                        if parent:
                            block_text = self._clean_text(parent.get_text(separator=" "))
                            if len(block_text) > 40 and block_text not in content_blocks:
                                content_blocks.append(block_text)

                if content_blocks:
                    job_description = "\n\n".join(content_blocks[:4])
                else:
                    # Fallback to main body text
                    body_text = self._clean_text(soup.get_text(separator=" "))
                    job_description = body_text[:1200]
        except Exception as e:
            logger.warning("Error fetching detail page %s: %s", detail_url, e)

        # 2. Fetch Direct Apply Link from apply_page.php?job_id=...
        try:
            apply_page_url = urljoin(self.BASE_URL, f"frontend/apply_page.php?job_id={job_id}")
            resp_apply = self.session.get(apply_page_url, timeout=10)
            if resp_apply.status_code == 200:
                soup_apply = BeautifulSoup(resp_apply.text, "html.parser")
                for a in soup_apply.find_all("a", href=True):
                    text = a.get_text(strip=True).lower()
                    href = a["href"].strip()
                    if text == "apply now" and not href.startswith("#") and not href.startswith("../"):
                        apply_link = href
                        break
        except Exception as e:
            logger.warning("Error fetching apply link for job %s: %s", job_id, e)

        return job_description, apply_link, refined_exp

    def scrape_portal_jobs_sync(self, max_jobs: int = 15) -> List[Dict[str, Any]]:
        """Synchronously parses job listings from thejobcompany.co.in portal."""
        logger.info("Scraping portal '%s' for up to %d job listings...", self.BASE_URL, max_jobs)
        jobs: List[Dict[str, Any]] = []

        try:
            resp = self.session.get(self.BASE_URL, timeout=12)
            if resp.status_code != 200:
                logger.error("Failed to fetch portal homepage: HTTP %d", resp.status_code)
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_="company-split")
            logger.info("Found %d job cards on portal homepage.", len(cards))

            for card in cards[:max_jobs]:
                try:
                    # 1. Title & Company
                    title_el = card.find(class_="company-title")
                    raw_title = title_el.get_text(strip=True) if title_el else ""
                    company, role = self._parse_company_and_role(raw_title)

                    # 2. Extract Card Attributes (Batch, Location, Qualification, Salary)
                    attributes = {}
                    for p in card.find_all("p"):
                        txt = p.get_text(strip=True)
                        if ":" in txt:
                            k, v = txt.split(":", 1)
                            attributes[k.strip().lower()] = v.strip()

                    batch = attributes.get("batch", "")
                    location = attributes.get("location", "India / Remote")
                    qualification = attributes.get("qualification", "")
                    salary = attributes.get("salary", "")

                    # 3. Locate detail link and extract job_id
                    detail_link = card.find("a", href=lambda h: h and "job_details" in h)
                    detail_rel = detail_link["href"] if detail_link else ""
                    detail_url = urljoin(self.BASE_URL, detail_rel)

                    job_id_match = re.search(r"job_id=(\d+)", detail_url)
                    job_id = job_id_match.group(1) if job_id_match else None

                    # 4. Fetch full JD & Apply Link
                    if job_id:
                        jd_text, apply_url, _ = self.fetch_job_details(job_id, detail_url)
                    else:
                        jd_text = f"Role: {role} at {company}. Qualification: {qualification}. Salary: {salary}"
                        apply_url = detail_url or self.BASE_URL

                    # 5. Derive Experience and Passing Out Year
                    passing_out_year = batch if batch else "Any"
                    experience_required = self._derive_experience_required(batch, role, jd_text)

                    jobs.append({
                        "job_id": job_id,
                        "title": role,
                        "company": company,
                        "experience_required": experience_required,
                        "passing_out_year": passing_out_year,
                        "job_description": jd_text if jd_text else f"Hiring for {role} at {company}. Location: {location}.",
                        "apply_link": apply_url,
                        "location": location,
                        "salary": salary,
                        "qualification": qualification,
                        "source": "live",
                        "portal": "thejobcompany"
                    })

                    # Small delay between job detail fetches
                    time.sleep(0.3)

                except Exception as card_err:
                    logger.warning("Error processing portal job card: %s", card_err)
                    continue

        except Exception as e:
            logger.error("Portal scraping encountered unexpected error: %s", e)

        logger.info("Successfully parsed %d jobs from %s.", len(jobs), self.BASE_URL)
        return jobs

    async def scrape_portal_jobs(self, max_jobs: int = 15) -> List[Dict[str, Any]]:
        """Asynchronously wraps the synchronous portal scraper."""
        return await asyncio.to_thread(self.scrape_portal_jobs_sync, max_jobs)

    def ingest_jobs_into_chroma(self, jobs: List[Dict[str, Any]]) -> int:
        """Embeds parsed portal jobs into ChromaDB under metadata source='live'."""
        if not jobs:
            return 0

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for job in jobs:
            job_id = f"portal_job_{job.get('job_id') or int(time.time()*1000)}"
            company = job.get("company", "Company")
            title = job.get("title", "Software Engineer")
            exp = job.get("experience_required", "Fresher")
            batch = job.get("passing_out_year", "")
            location = job.get("location", "")
            salary = job.get("salary", "")
            url = job.get("apply_link", "")
            jd = job.get("job_description", "")

            # Format rich searchable document
            doc_text = (
                f"Company: {company}\n"
                f"Role: {title}\n"
                f"Experience Required: {exp}\n"
                f"Passing Out Year: {batch}\n"
                f"Location: {location}\n"
                f"Salary: {salary}\n"
                f"Apply Link: {url}\n"
                f"Job Description: {jd}"
            )

            documents.append(doc_text)
            metadatas.append({
                "source": "live",
                "portal": "thejobcompany",
                "company": company,
                "title": title,
                "experience_level": exp,
                "passing_out_year": batch,
                "url": url,
                "location": location,
                "salary": salary,
                "timestamp": int(time.time())
            })
            ids.append(job_id)

        chroma_manager.add_job_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info("Embedded %d portal jobs into ChromaDB under source='live'.", len(documents))
        return len(documents)

    async def scrape_and_ingest_live(self, max_jobs: int = 15) -> Tuple[List[Dict[str, Any]], int]:
        """Scrapes portal jobs and embeds them directly into ChromaDB."""
        jobs = await self.scrape_portal_jobs(max_jobs=max_jobs)
        embedded_count = self.ingest_jobs_into_chroma(jobs)
        return jobs, embedded_count


job_company_scraper = JobCompanyScraperService()
