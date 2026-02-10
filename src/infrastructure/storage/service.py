"""
File storage service abstraction.
"""
import os
import uuid
import logging
from typing import Optional, BinaryIO
from dataclasses import dataclass

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of file upload operation."""
    success: bool
    url: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None


class StorageService:
    """
    File storage service abstraction.

    Works with Django's default storage backend (local, S3, etc.).
    """

    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "text/csv"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def upload(
        self,
        file: BinaryIO,
        path: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a file to storage.

        Args:
            file: File-like object to upload
            path: Directory path (e.g., "avatars/2026/02")
            filename: Optional filename (auto-generated if not provided)
            content_type: Optional content type for validation

        Returns:
            UploadResult with URL and path
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                ext = self._get_extension_from_content_type(content_type or "")
                filename = f"{uuid.uuid4().hex}{ext}"

            full_path = os.path.join(path, filename)

            # Read content
            content = file.read()

            # Validate size
            if len(content) > self.MAX_FILE_SIZE:
                return UploadResult(
                    success=False,
                    error=f"File too large. Max size: {self.MAX_FILE_SIZE // 1024 // 1024}MB"
                )

            # Save file
            saved_path = default_storage.save(full_path, ContentFile(content))
            url = default_storage.url(saved_path)

            logger.info(f"File uploaded: {saved_path}")
            return UploadResult(success=True, url=url, path=saved_path)

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return UploadResult(success=False, error=str(e))

    def delete(self, path: str) -> bool:
        """Delete a file from storage."""
        try:
            if default_storage.exists(path):
                default_storage.delete(path)
                logger.info(f"File deleted: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return default_storage.exists(path)

    def get_url(self, path: str) -> Optional[str]:
        """Get URL for a file."""
        if default_storage.exists(path):
            return default_storage.url(path)
        return None

    def get_size(self, path: str) -> int:
        """Get file size in bytes."""
        if default_storage.exists(path):
            return default_storage.size(path)
        return 0

    def validate_image(self, content_type: str) -> bool:
        """Validate if content type is allowed for images."""
        return content_type in self.ALLOWED_IMAGE_TYPES

    def validate_document(self, content_type: str) -> bool:
        """Validate if content type is allowed for documents."""
        return content_type in self.ALLOWED_DOCUMENT_TYPES

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "text/plain": ".txt",
            "text/csv": ".csv",
        }
        return extensions.get(content_type, "")


storage_service = StorageService()
