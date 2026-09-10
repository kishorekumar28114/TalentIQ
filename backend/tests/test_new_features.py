"""Unit and Integration tests for TheJobCompany Portal Scraper and Experience-Based Smart Matching."""

import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.job_company_scraper import job_company_scraper
from app.db.chroma import chroma_manager


def test_custom_portal_scraper_direct():
    print("\n--- Testing JobCompanyScraperService directly ---")
    jobs = job_company_scraper.scrape_portal_jobs_sync(max_jobs=3)
    assert len(jobs) > 0, "Should have scraped at least 1 job"
    
    for j in jobs:
        print(f"Company: {j['company']}")
        print(f"Title: {j['title']}")
        print(f"Experience Required: {j['experience_required']}")
        print(f"Passing Out Year: {j['passing_out_year']}")
        print(f"Apply Link: {j['apply_link']}")
        print(f"JD Snippet: {j['job_description'][:100]}...")
        assert j["company"], "Company should not be empty"
        assert j["title"], "Title should not be empty"
        assert j["experience_required"], "Experience required should be extracted"
        assert j["passing_out_year"], "Passing out year should be extracted"
        assert j["apply_link"], "Apply link should be extracted"
        assert j["job_description"], "Job description should be extracted"

    # Test ChromaDB embedding
    count = job_company_scraper.ingest_jobs_into_chroma(jobs)
    assert count == len(jobs)
    print(f"Successfully ingested {count} portal jobs into ChromaDB with source='live'.")


def test_experience_reranking():
    print("\n--- Testing Experience-Based Reranking ---")
    test_jobs = [
        {
            "document": "Company: Tech Corp\nRole: Senior Principal Distributed Systems Architect\nExperience: 8+ years",
            "metadata": {"title": "Senior Principal Systems Architect", "experience_level": "8+ Years (Senior)", "company": "Tech Corp"},
            "distance": 0.20,
            "similarity_score": 0.80,
            "source": "excel"
        },
        {
            "document": "Company: Startup Inc\nRole: Junior Software Engineer Intern\nExperience: Fresher / 0-1 years",
            "metadata": {"title": "Junior Software Engineer", "experience_level": "Fresher (0-1 Years)", "company": "Startup Inc"},
            "distance": 0.25,
            "similarity_score": 0.75,
            "source": "excel"
        }
    ]

    # When candidate is Fresher
    fresher_ranks = chroma_manager.rerank_by_experience(test_jobs, user_experience="Fresher", top_k=2)
    print("Fresher top match:", fresher_ranks[0]["metadata"]["title"])
    assert "Junior" in fresher_ranks[0]["metadata"]["title"] or "Intern" in fresher_ranks[0]["metadata"]["title"], \
        "Fresher should match Junior role over Senior Principal role"

    # When candidate is Senior
    senior_ranks = chroma_manager.rerank_by_experience(test_jobs, user_experience="8+ Years (Senior)", top_k=2)
    print("Senior top match:", senior_ranks[0]["metadata"]["title"])
    assert "Senior" in senior_ranks[0]["metadata"]["title"], \
        "Senior candidate should match Senior Principal role over Junior role"


def test_api_endpoints():
    print("\n--- Testing FastAPI Endpoints ---")
    with TestClient(app) as client:
        # 1. Scrape Portal endpoint
        r = client.post("/api/data/scrape-portal?max_jobs=2")
        print(f"POST /api/data/scrape-portal: {r.status_code}")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["jobs_scraped"] > 0
        assert len(data["jobs"]) > 0
        print(f"Scraped {data['jobs_scraped']} portal jobs via API.")

        # 2. Match Resume endpoint with Experience payload
        dummy_resume = (
            b"ALEX SMITH\n"
            b"Aspiring Full-Stack Software Developer\n"
            b"Education: B.Tech Computer Science (Graduating 2026)\n"
            b"Skills: Python, FastAPI, React, JavaScript, PostgreSQL, Docker\n"
            b"Projects: Built automated job matcher web application.\n"
        )
        files = {"file": ("alex_smith_resume.txt", dummy_resume, "text/plain")}
        payload = {"experience": "Fresher"}
        r_match = client.post("/api/match/resume", files=files, data=payload)
        print(f"POST /api/match/resume (Fresher): {r_match.status_code}")
        assert r_match.status_code == 200
        match_data = r_match.json()
        assert match_data["success"] is True
        assert match_data["provided_experience"] == "Fresher"
        assert len(match_data["top_company_fits"]) > 0
        print(f"Top fit 1: {match_data['top_company_fits'][0]['company']} - {match_data['top_company_fits'][0]['role']}")
        print(f"Why fit: {match_data['top_company_fits'][0]['why_perfect_fit'][:120]}...")

        # 3. Match Resume endpoint with legacy/no experience (should default to Fresher safely)
        files2 = {"file": ("legacy_resume.txt", dummy_resume, "text/plain")}
        r_legacy = client.post("/api/match/resume", files=files2)
        print(f"POST /api/match/resume (No experience parameter): {r_legacy.status_code}")
        assert r_legacy.status_code == 200
        assert r_legacy.json()["provided_experience"] == "Fresher"


if __name__ == "__main__":
    test_custom_portal_scraper_direct()
    test_experience_reranking()
    test_api_endpoints()
    print("\n>>> ALL NEW FEATURE TESTS PASSED! <<<")
