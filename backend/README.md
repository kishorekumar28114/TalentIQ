# 🚀 Job-Matcher: Production-Grade Agentic RAG Backend

A high-performance, asynchronous FastAPI backend powering an **Agentic RAG Job Matchmaking Application**. Built with **FastAPI**, **ChromaDB**, **Motor (Async MongoDB)**, **LangGraph**, **Langchain-Groq**, **DuckDuckGo-Search (`ddgs`)**, and **Cloudinary**.

---

## 🏛️ System Architecture

```mermaid
graph TD
    Client["Client / Frontend"] -->|POST /api/match/resume| MatchRoute["Resume Match Router"]
    Client -->|POST /api/data/trigger-live| ScraperRoute["Live Data Trigger Router"]
    Client -->|POST /api/chat| ChatRoute["Agent Chat Router"]

    subgraph Storage & Cloud
        Cloudinary["Cloudinary (PDF / Image Hosting)"]
        MongoDB["MongoDB (Motor Checkpointer & Resumes)"]
        ChromaDB[("ChromaDB 'job_market'\n(source: 'live' | 'excel')")]
    end

    subgraph External Engines
        DDGS["DuckDuckGo Search (ddgs)"]
        Groq["Groq API (Llama 3 70B)"]
    end

    subgraph Agentic Layer
        LangGraph["LangGraph Stateful Agent"]
        ChromaTool["ChromaJobSearchTool"]
        WebTool["WebSearchTool (ddgs)"]
    end

    MatchRoute -->|1. Upload File| Cloudinary
    MatchRoute -->|2. Extract Profile JSON| Groq
    MatchRoute -->|3. Query Vector DB (Live -> Excel Fallback)| ChromaDB
    MatchRoute -->|4. Fit Analysis (Top 3)| Groq
    MatchRoute -->|5. Save State| MongoDB

    ScraperRoute -->|1. Delete source:live| ChromaDB
    ScraperRoute -->|2. Scrape Company Jobs & Tech Stacks| DDGS
    ScraperRoute -->|3. Upsert live records| ChromaDB

    ChatRoute --> LangGraph
    LangGraph -->|Persistent Memory| MongoDB
    LangGraph --> ChromaTool
    ChromaTool --> ChromaDB
    LangGraph -->|Fallback if not in Chroma| WebTool
    WebTool --> DDGS
    LangGraph --> Groq
```

---

## 🔑 Core Features & Architectural Requirements

### 1. Vector Database (ChromaDB) Layer
- **Collection**: `job_market`
- **Two-Tier Data Strategy**:
  - `metadata={"source": "excel"}`: Permanent baseline jobs serving as the rock-solid fallback dataset.
  - `metadata={"source": "live"}`: Dynamic scraped job postings and tech stack blogs.
- **Fallback Mechanism**: When matching candidate profiles, the system queries `'live'` records first. If distance is above threshold or no live records exist, it automatically falls back to `'excel'` records.

### 2. Live Scraping Engine (`ddgs`)
- **Endpoint**: `POST /api/data/trigger-live`
- **Automated Workflow**:
  1. Purges all existing ChromaDB records where `metadata={"source": "live"}`.
  2. Iterates across a static list of target tech companies (`Google`, `Microsoft`, `Amazon`, `Meta`, `Apple`, `Netflix`, `Stripe`, `Uber`, `Databricks`, `OpenAI`).
  3. Scrapes real-time hiring posts and engineering tech stack blogs via DuckDuckGo (`ddgs`).
  4. Generates embeddings and ingests fresh records into ChromaDB with `metadata={"source": "live"}`.

### 3. Resume Processing & Matchmaking (RAG)
- **Endpoint**: `POST /api/match/resume` (Multipart Form File Upload: PDF, image, text)
- **Workflow**:
  1. Uploads file to Cloudinary and acquires a permanent `secure_url`.
  2. Extracts document text and invokes Groq API (`llama3-70b-8192` / `llama-3.3-70b-versatile`) to extract structured profile JSON:
     - Candidate Name, Preferred Roles, Years of Experience, Technical Skills, Soft Skills, Domain Experience, and Summary.
  3. Queries ChromaDB using candidate profile vectors with **live-first priority** and seamless **excel fallback**.
  4. Feeds top matched company records back to Groq to synthesize an in-depth, personalized **"Why you are a perfect fit"** evaluation for the **top 3 companies**.
  5. Saves candidate record to MongoDB.

### 4. LangGraph Agent (Conversational Interface)
- **Endpoint**: `POST /api/chat`
- **Stateful Memory**: Powered by LangGraph's checkpointer backed by **MongoDB** (with in-memory fallback for local development).
- **Tools**:
  - `search_job_market_database`: Queries internal ChromaDB `job_market` collection.
  - `search_web_for_jobs`: Live DuckDuckGo web search.
- **Autonomous Decision Logic**:
  - If a user inquires about a company or tech stack, the agent first inspects ChromaDB.
  - If the company is **not present** in the internal ChromaDB context, the agent **autonomously invokes `search_web_for_jobs`** to search live job postings and engineering blogs across the internet, returning comprehensive citations and links.

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & lifecycle
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment validation
│   │   └── logging.py           # Structured logging setup
│   ├── db/
│   │   ├── mongodb.py           # Motor (Async) & PyMongo connection manager
│   │   └── chroma.py            # ChromaDB two-tier vector database manager
│   ├── services/
│   │   ├── scraper_service.py   # DuckDuckGo live job & blog scraper
│   │   ├── cloudinary_service.py# Cloudinary async media uploader
│   │   ├── resume_parser.py     # PyPDF text extraction & Groq JSON profiling
│   │   └── matchmaking_service.py # RAG matching & Groq fit synthesis
│   ├── agent/
│   │   ├── state.py             # LangGraph state schema
│   │   ├── tools.py             # ChromaDB search & DuckDuckGo web search tools
│   │   ├── checkpointer.py      # MongoDB state checkpointer factory
│   │   └── graph.py             # LangGraph state machine compilation
│   ├── schemas/
│   │   ├── common.py            # Generic API & Health schemas
│   │   ├── data.py              # Live trigger & seed response schemas
│   │   ├── match.py             # Resume & matchmaking schemas
│   │   └── chat.py              # Conversational chat schemas
│   └── api/
│       └── api_v1/
│           ├── router.py        # Central API v1 router
│           └── endpoints/
│               ├── health.py    # GET /api/health
│               ├── data.py      # POST /api/data/trigger-live, POST /api/data/seed-base
│               ├── match.py     # POST /api/match/resume
│               └── chat.py      # POST /api/chat
├── data/
│   ├── seed_jobs.json           # Permanent baseline Excel jobs
│   └── chroma/                  # Persistent ChromaDB vector index
├── tests/
│   └── test_suite.py            # Comprehensive verification suite
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

---

## 🛠️ Installation & Quickstart

### 1. Clone & Activate Virtual Environment
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```

| Key | Description | Default / Example |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Groq Console API Key | `gsk_...` |
| `GROQ_MODEL` | Primary Llama 3 model | `llama-3.3-70b-versatile` |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | MongoDB database name | `job_matcher_db` |
| `CLOUDINARY_CLOUD_NAME`| Cloudinary Cloud Name | `your_cloud_name` |
| `CLOUDINARY_API_KEY` | Cloudinary API Key | `your_api_key` |
| `CLOUDINARY_API_SECRET`| Cloudinary API Secret | `your_api_secret` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB vector path | `./data/chroma` |
| `SIMILARITY_DISTANCE_THRESHOLD` | Fallback threshold | `0.85` |

### 4. Run Verification Test Suite
```bash
python tests/test_suite.py
```

### 5. Launch FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at:
👉 **`http://127.0.0.1:8000/docs`**

---

## 📡 API Reference & Examples

### 1. Trigger Live Data Scraping
**`POST /api/data/trigger-live`**
Purges existing `source="live"` records, searches DuckDuckGo for all target companies, and embeds results into ChromaDB.
```bash
curl -X POST "http://127.0.0.1:8000/api/data/trigger-live"
```

### 2. Upload Resume & Match (RAG)
**`POST /api/match/resume`**
Uploads a candidate PDF/Image, extracts profile JSON via Groq, matches against ChromaDB with live-first priority and Excel fallback, and synthesizes "Why you are a perfect fit" summaries for the top 3 companies.
```bash
curl -X POST "http://127.0.0.1:8000/api/match/resume" \
  -F "file=@/path/to/resume.pdf"
```

### 3. Conversational Agent with Memory
**`POST /api/chat`**
Engages in a multi-turn conversation backed by MongoDB memory. Autonomously triggers `search_web_for_jobs` if a company is absent from ChromaDB.
```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What jobs and tech stack does Palantir have?",
    "thread_id": "session_user_42"
  }'
```

### 4. System Diagnostics
**`GET /api/health`**
Returns collection counts for `live` and `excel` records, MongoDB connection status, Groq configuration, and Cloudinary status.
```bash
curl -X GET "http://127.0.0.1:8000/api/health"
```
