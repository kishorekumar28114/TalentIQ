"""Authentication endpoints: Register, Login, Current User Profile, and Resume Mapping."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.core.logging import logger
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.db.mongodb import mongo_manager
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse
)

router = APIRouter(prefix="/auth")


def _format_user_response(user_dict: dict) -> UserResponse:
    """Safely converts MongoDB user document to public UserResponse schema."""
    user_id = str(user_dict.get("_id") or user_dict.get("id"))
    resume_data = user_dict.get("resume")
    return UserResponse(
        id=user_id,
        email=user_dict["email"],
        full_name=user_dict.get("full_name", "User"),
        created_at=user_dict.get("created_at"),
        resume=resume_data
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register(payload: UserRegisterRequest):
    """Registers a new candidate user in MongoDB and returns JWT access token."""
    normalized_email = payload.email.lower().strip()
    
    # Check if email is already registered
    existing_user = await mongo_manager.get_user_by_email(normalized_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please log in."
        )

    # Hash password with bcrypt
    hashed_pwd = hash_password(payload.password)

    user_doc = {
        "email": normalized_email,
        "password_hash": hashed_pwd,
        "full_name": payload.full_name.strip(),
        "resume": None
    }

    created_user = await mongo_manager.create_user(user_doc)
    user_id = str(created_user.get("_id") or created_user.get("id"))

    # Generate JWT token with user ID subject
    token = create_access_token({"sub": user_id, "email": normalized_email})

    logger.info("New user successfully registered: '%s' (id: %s)", normalized_email, user_id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_response(created_user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login with email and password"
)
async def login(payload: UserLoginRequest):
    """Authenticates user credentials and returns JWT access token with profile."""
    normalized_email = payload.email.lower().strip()

    user = await mongo_manager.get_user_by_email(normalized_email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = str(user.get("_id") or user.get("id"))
    token = create_access_token({"sub": user_id, "email": normalized_email})

    logger.info("User logged in successfully: '%s' (id: %s)", normalized_email, user_id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_response(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile and mapped Cloudinary resume"
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user document, including their mapped Cloudinary resume and profile."""
    return _format_user_response(current_user)


@router.delete(
    "/resume",
    status_code=status.HTTP_200_OK,
    summary="Unlink/delete resume mapping for current user"
)
async def delete_my_resume(current_user: dict = Depends(get_current_user)):
    """Removes the resume mapping from the current authenticated user's MongoDB record."""
    user_id = str(current_user.get("_id") or current_user.get("id"))
    success = await mongo_manager.remove_user_resume(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not remove resume mapping."
        )
    return {"success": True, "message": "Resume unlinked successfully."}
