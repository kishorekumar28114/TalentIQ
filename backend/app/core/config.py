"""Application configuration using Pydantic Settings."""

import os
from typing import List, Union
from dotenv import load_dotenv, find_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Automatically find and load .env file from working directory or parent directories
env_path = find_dotenv(usecwd=True)
if not env_path or not os.path.exists(env_path):
    env_path = os.path.join(BACKEND_DIR, ".env")
load_dotenv(env_path, override=True)


class Settings(BaseSettings):
    """Global configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Job-Matcher Agentic RAG API"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Groq API Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_FALLBACK_MODEL: str = "openai/gpt-oss-20b"

    # JWT Authentication
    JWT_SECRET_KEY: str = "job_matcher_super_secret_jwt_key_2026_dev"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "job_matcher_db"

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ChromaDB Vector Storage
    CHROMA_PERSIST_DIRECTORY: str = os.path.join(BACKEND_DIR, "data", "chroma")
    CHROMA_COLLECTION_NAME: str = "job_market"

    # Matchmaking & Scraping Configuration
    SIMILARITY_DISTANCE_THRESHOLD: float = 0.85  # Low distance = high similarity in ChromaDB L2/cosine
    BASE_SEED_FILE: str = os.path.join(BACKEND_DIR, "data", "seed_jobs.json")

    @field_validator("CHROMA_PERSIST_DIRECTORY", mode="after")
    @classmethod
    def resolve_chroma_path(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.normpath(os.path.join(BACKEND_DIR, v))
        return v

    @field_validator("BASE_SEED_FILE", mode="after")
    @classmethod
    def resolve_seed_path(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.normpath(os.path.join(BACKEND_DIR, v))
        return v

    # Predefined static list of companies for live scraping
    TARGET_COMPANIES: Union[List[str], str] = [
        "Google",
        "Microsoft",
        "Amazon",
        "Meta",
        "Apple",
        "Netflix",
        "Stripe",
        "Uber",
        "Databricks",
        "OpenAI"
    ]

    @field_validator("TARGET_COMPANIES", mode="before")
    @classmethod
    def parse_target_companies(cls, v):
        if isinstance(v, str):
            return [company.strip() for company in v.split(",") if company.strip()]
        return v

    @property
    def has_groq_key(self) -> bool:
        return bool(self.GROQ_API_KEY and not self.GROQ_API_KEY.startswith("your_"))

    @property
    def has_cloudinary(self) -> bool:
        return bool(
            self.CLOUDINARY_CLOUD_NAME
            and self.CLOUDINARY_API_KEY
            and self.CLOUDINARY_API_SECRET
            and not self.CLOUDINARY_CLOUD_NAME.startswith("your_")
        )


settings = Settings()
