"""Resume text extractor and Groq LLM parser (llama3-70b-8192 / llama-3.3-70b-versatile).

Workflow:
  1. Extract raw text from PDF bytes using pypdf.
  2. Invoke Groq API with structured JSON output instructions.
  3. Extract key skills, experience, and role preferences into CandidateProfile.
"""

import io
import json
import re
from typing import Optional
from pypdf import PdfReader
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.core.logging import logger
from app.schemas.match import CandidateProfile


class ResumeParserService:
    """Parses resumes using pypdf text extraction and Groq LLM extraction."""

    def __init__(self):
        self._groq_client = None

    def _get_groq_llm(self, model: Optional[str] = None):
        """Initializes ChatGroq client with selected model."""
        if not settings.has_groq_key:
            return None
        target_model = model or settings.GROQ_MODEL
        try:
            return ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=target_model,
                temperature=0.1
            )
        except Exception as e:
            logger.warning("Error initializing ChatGroq with model %s: %s", target_model, e)
            if target_model != settings.GROQ_FALLBACK_MODEL:
                logger.info("Retrying with fallback model %s...", settings.GROQ_FALLBACK_MODEL)
                return ChatGroq(
                    groq_api_key=settings.GROQ_API_KEY,
                    model_name=settings.GROQ_FALLBACK_MODEL,
                    temperature=0.1
                )
            raise

    def extract_text_from_bytes(self, file_bytes: bytes, filename: str) -> str:
        """Extracts plain text from PDF or raw bytes."""
        text = ""
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_idx + 1} ---\n" + page_text
                logger.info("Extracted %d characters across %d pages from PDF '%s'.", len(text), len(reader.pages), filename)
            except Exception as e:
                logger.error("Failed to parse PDF pages: %s. Attempting raw text decode.", e)
                try:
                    text = file_bytes.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""
        else:
            # Plain text, markdown, or code file
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = ""

        return text.strip()

    async def parse_resume(self, file_bytes: bytes, filename: str, file_url: str) -> CandidateProfile:
        """Extracts text and uses Groq to structure candidate profile into JSON."""
        raw_text = self.extract_text_from_bytes(file_bytes, filename)

        if not raw_text:
            raw_text = f"Resume document uploaded at URL: {file_url} (Filename: {filename})"

        # If Groq API key is configured, use Groq LLM
        if settings.has_groq_key:
            try:
                llm = self._get_groq_llm()
                prompt = (
                    "You are an expert technical recruiting AI. Analyze the following candidate resume text.\n"
                    "Extract their profile and return ONLY valid JSON matching this schema:\n"
                    "{\n"
                    '  "name": "Candidate Name",\n'
                    '  "role_preferences": ["Role 1", "Role 2"],\n'
                    '  "years_of_experience": 4.5,\n'
                    '  "technical_skills": ["Python", "FastAPI", "PostgreSQL", ...],\n'
                    '  "soft_skills": ["Leadership", "Communication", ...],\n'
                    '  "domain_experience": ["Fintech", "Distributed Systems", ...],\n'
                    '  "summary": "Concise 2-sentence executive summary of background and technical identity"\n'
                    "}\n\n"
                    "Resume Document Text:\n"
                    f"\"\"\"\n{raw_text[:12000]}\n\"\"\"\n\n"
                    "DO NOT output markdown code fences (```json or ```). Output ONLY the raw JSON object."
                )

                messages = [
                    SystemMessage(content="You are a precise JSON-only resume parser assistant."),
                    HumanMessage(content=prompt)
                ]

                try:
                    response = await llm.ainvoke(messages)
                except Exception as invoke_err:
                    logger.warning("Resume parsing failed with %s: %s. Retrying with fallback model %s...", settings.GROQ_MODEL, invoke_err, settings.GROQ_FALLBACK_MODEL)
                    fallback_llm = ChatGroq(
                        groq_api_key=settings.GROQ_API_KEY,
                        model_name=settings.GROQ_FALLBACK_MODEL,
                        temperature=0.1
                    )
                    response = await fallback_llm.ainvoke(messages)

                content = response.content.strip()

                # Clean markdown blocks if present
                content = re.sub(r"^```json\s*", "", content)
                content = re.sub(r"^```\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

                parsed_json = json.loads(content)
                return CandidateProfile(**parsed_json)

            except Exception as e:
                logger.error("Groq resume parsing failed: %s. Falling back to heuristic extractor.", e)

        # Heuristic fallback if Groq is offline or API key is pending
        return self._heuristic_parse(raw_text, filename)

    def _heuristic_parse(self, text: str, filename: str) -> CandidateProfile:
        """Rule-based extractor for local/offline testing."""
        logger.info("Executing heuristic resume parsing...")
        common_tech = [
            "Python", "Java", "Go", "Golang", "C++", "C#", "Rust", "JavaScript", "TypeScript",
            "FastAPI", "Django", "Flask", "React", "Node.js", "Express", "Kubernetes", "Docker",
            "AWS", "GCP", "Azure", "PostgreSQL", "MongoDB", "Redis", "Kafka", "GraphQL", "PyTorch",
            "TensorFlow", "LangChain", "ChromaDB", "Elasticsearch", "Distributed Systems", "REST"
        ]
        found_skills = [s for s in common_tech if re.search(rf"\b{re.escape(s)}\b", text, re.IGNORECASE)]
        if not found_skills:
            found_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Distributed Systems"]

        # Estimate years
        exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", text, re.IGNORECASE)
        years = float(exp_match.group(1)) if exp_match else 3.0

        return CandidateProfile(
            name="Sample Candidate",
            role_preferences=["Senior Backend Engineer", "AI Platform Engineer", "Full Stack Developer"],
            years_of_experience=years,
            technical_skills=found_skills,
            soft_skills=["System Design", "Cross-functional Collaboration", "Technical Mentorship"],
            domain_experience=["Cloud Infrastructure", "API Design", "Distributed Systems"],
            summary=f"Experienced software engineer with proficiency in {', '.join(found_skills[:5])}."
        )


resume_parser = ResumeParserService()
