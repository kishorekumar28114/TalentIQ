from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from app.core.logging import logger
from app.core.security import get_optional_current_user
from app.services.matchmaking_service import matchmaking_service
from app.schemas.match import ResumeMatchResponse

router = APIRouter()

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
    "application/octet-stream"
]


@router.post(
    "/match/resume",
    response_model=ResumeMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Resume, Match with ChromaDB, and Generate Fit Summaries"
)
async def match_resume(
    file: UploadFile = File(..., description="PDF, image, or text resume document"),
    experience: str = Form("Fresher", description="Current Experience (e.g., Fresher / 2+ Years)"),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Executes the end-to-end Resume Matchmaking pipeline:

    1. **File Upload**: Reads uploaded resume and securely hosts it on Cloudinary (mapped to user profile if authenticated).
    2. **Groq Extraction**: Extracts key skills, experience, and role preferences in JSON format.
    3. **Experience-Aware Two-Tier ChromaDB Retrieval**:
       - Filters and prioritizes jobs aligned with the candidate's provided experience level.
       - Searches 'live' scraped jobs first (DuckDuckGo + TheJobCompany portal).
       - If match scores are poor (distance > threshold) or no live records exist, seamlessly falls back to permanent 'excel' baseline data.
    4. **Personalized Fit Synthesis**: Uses Groq API to synthesize a tailored 'Why you are a perfect fit' summary for the top 3 companies with experience alignment.
    5. **User Mapping**: Automatically links the resume URL and extracted profile to the authenticated user's MongoDB record.
    """
    user_id = str(current_user.get("_id") or current_user.get("id")) if current_user else None
    logger.info(
        "Received resume file upload: '%s' (content_type: %s, experience: %s, user: %s)",
        file.filename, file.content_type, experience, user_id
    )

    # Validate file presence
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload."
        )

    try:
        # Read file contents into memory
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        logger.info("Processing uploaded resume (%d bytes) with experience '%s'...", len(file_bytes), experience)
        match_result = await matchmaking_service.match_resume_file(
            file_bytes=file_bytes,
            filename=file.filename,
            experience=experience,
            user_id=user_id
        )
        return match_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Resume matchmaking pipeline failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the resume: {str(e)}"
        )
    finally:
        await file.close()
