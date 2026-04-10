"""
Storage utility functions.
"""
import os
import uuid
from datetime import datetime


def generate_upload_path(instance, filename: str, prefix: str = "") -> str:
    """
    Generate upload path with date-based organization.

    Usage in model:
        avatar = models.ImageField(
            upload_to=lambda i, f: generate_upload_path(i, f, "avatars")
        )

    Results in paths like: avatars/2026/02/abc123.jpg
    """
    ext = get_file_extension(filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date_path = datetime.now().strftime("%Y/%m")

    if prefix:
        return os.path.join(prefix, date_path, unique_name)
    return os.path.join(date_path, unique_name)


def get_file_extension(filename: str) -> str:
    """Get file extension including the dot."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be safe for storage.

    Removes special characters and limits length.
    """
    import re

    # Get extension
    name, ext = os.path.splitext(filename)

    # Remove special characters
    name = re.sub(r'[^\w\-]', '_', name)

    # Limit length
    name = name[:100]

    return f"{name}{ext}"


def get_content_type(filename: str) -> str:
    """Guess content type from filename."""
    import mimetypes
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"
