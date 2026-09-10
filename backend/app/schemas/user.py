"""Schemas for User model, authentication, and Cloudinary resume mapping."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.schemas.match import CandidateProfile, CompanyFitItem


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user."""
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: str = Field(..., min_length=2, description="Candidate full name")


class UserLoginRequest(BaseModel):
    """Payload for logging into an existing account."""
    email: EmailStr = Field(..., description="Account email address")
    password: str = Field(..., description="Account password")


class CloudinaryResumeInfo(BaseModel):
    """Cloudinary asset metadata and extracted profile mapped to the user."""
    cloudinary_url: str = Field(..., description="Public/secure URL of resume document hosted in Cloudinary")
    cloudinary_public_id: Optional[str] = Field(default=None, description="Cloudinary asset public ID")
    filename: Optional[str] = Field(default=None, description="Original uploaded filename")
    uploaded_at: Optional[str] = Field(default=None, description="ISO timestamp of upload")
    candidate_profile: Optional[CandidateProfile] = Field(default=None, description="Groq-parsed structured profile")
    top_company_fits: Optional[List[CompanyFitItem]] = Field(default_factory=list, description="Latest matched top 3 companies")


class UserResponse(BaseModel):
    """Public user profile with mapped Cloudinary resume."""
    id: str = Field(..., description="MongoDB ObjectId string")
    email: EmailStr
    full_name: str
    created_at: Optional[str] = None
    resume: Optional[CloudinaryResumeInfo] = None


class TokenResponse(BaseModel):
    """JWT Bearer authentication response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
