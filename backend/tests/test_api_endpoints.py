"""FastAPI Endpoints Integration Test using TestClient."""

import os
import sys
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app


def test_api():
    print("Testing FastAPI endpoints using TestClient...")
    with TestClient(app) as client:
        # 1. Root
        r = client.get("/")
        print(f"GET /: {r.status_code} - {r.json().get('service')}")
        assert r.status_code == 200

        # 2. Health
        r = client.get("/api/health")
        print(f"GET /api/health: {r.status_code} - {r.json()}")
        assert r.status_code == 200
        data = r.json()
        assert data["chromadb_connected"] is True
        assert data["chromadb_total_records"] > 0

        # 3. Seed Base
        r = client.post("/api/data/seed-base")
        print(f"POST /api/data/seed-base: {r.status_code} - {r.json().get('message')}")
        assert r.status_code == 200

        # 4. Resume Match
        dummy_resume = (
            b"JANE DOE\n"
            b"Staff Machine Learning & Backend Engineer\n"
            b"Skills: Python, PyTorch, FastAPI, Kubernetes, Distributed Systems, Ray\n"
            b"Experience: 6 years building distributed inference pipelines.\n"
        )
        files = {"file": ("jane_doe_resume.txt", dummy_resume, "text/plain")}
        r = client.post("/api/match/resume", files=files)
        print(f"POST /api/match/resume: {r.status_code}")
        assert r.status_code == 200
        match_data = r.json()
        print(f"  Source Used: {match_data['source_used']}")
        print(f"  Cloudinary URL: {match_data['cloudinary_url']}")
        print(f"  Top Fits: {len(match_data['top_company_fits'])} companies")

        # 5. Chat Endpoint
        chat_payload = {
            "message": "What roles are available at Microsoft?",
            "thread_id": "test_thread_fastapi_01"
        }
        r = client.post("/api/chat", json=chat_payload)
        print(f"POST /api/chat: {r.status_code}")
        assert r.status_code == 200
        chat_data = r.json()
        print(f"  Thread ID: {chat_data['thread_id']}")
        print(f"  Agent Response: {chat_data['response'][:150]}...")

    print("\n>>> ALL FASTAPI ENDPOINTS VERIFIED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    test_api()
