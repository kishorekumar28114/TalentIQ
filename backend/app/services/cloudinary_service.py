"""Cloudinary integration service for uploading resume documents and images."""

import os
import uuid
import asyncio
from typing import Dict, Any, Tuple, Optional
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.logging import logger


UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))


class CloudinaryService:
    """Manages document uploads to Cloudinary with reliable local fallback."""

    def __init__(self):
        if settings.has_cloudinary:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            logger.info("Cloudinary service initialized with cloud name: %s", settings.CLOUDINARY_CLOUD_NAME)
        else:
            logger.warning(
                "Cloudinary credentials missing in .env. Resumes will be stored and served locally."
            )

    def _save_locally(self, file_bytes: bytes, filename: str, folder_suffix: Optional[str] = None) -> Dict[str, Any]:
        """Saves file to backend/uploads and returns local preview URL."""
        sub_folder = os.path.join(UPLOAD_DIR, "resumes", folder_suffix or "")
        os.makedirs(sub_folder, exist_ok=True)

        unique_id = uuid.uuid4().hex[:10]
        clean_filename = os.path.basename(filename).replace(" ", "_")
        stored_filename = f"{unique_id}_{clean_filename}"
        file_path = os.path.join(sub_folder, stored_filename)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        rel_url = f"resumes/{folder_suffix}/{stored_filename}".replace("\\", "/") if folder_suffix else f"resumes/{stored_filename}"
        local_url = f"http://localhost:8000/uploads/{rel_url}"
        logger.info("Saved resume locally: %s -> %s", file_path, local_url)

        return {
            "secure_url": local_url,
            "public_id": f"local/{rel_url}",
            "resource_type": "local",
            "bytes": len(file_bytes),
            "is_local": True
        }

    def _upload_sync(self, file_bytes: bytes, filename: str, folder_suffix: Optional[str] = None) -> Dict[str, Any]:
        """Uploads file to Cloudinary if available, falling back safely to local static serving."""
        # Always persist a local copy so user can immediately view/verify their uploaded PDF
        local_res = self._save_locally(file_bytes, filename, folder_suffix)

        if not settings.has_cloudinary:
            return local_res

        target_folder = f"job_matcher_resumes/{folder_suffix}" if folder_suffix else "job_matcher_resumes"

        try:
            # Cloudinary upload
            upload_result = cloudinary.uploader.upload(
                file_bytes,
                folder=target_folder,
                resource_type="auto",
                use_filename=True,
                unique_filename=True
            )
            logger.info("Cloudinary upload successful: %s", upload_result.get("secure_url"))
            return upload_result
        except Exception as e:
            logger.warning("Cloudinary upload API failed (%s). Using accessible local URL instead.", e)
            return local_res

    async def upload_file(self, file_bytes: bytes, filename: str, folder_suffix: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronous wrapper for upload."""
        return await asyncio.to_thread(self._upload_sync, file_bytes, filename, folder_suffix)


cloudinary_service = CloudinaryService()
