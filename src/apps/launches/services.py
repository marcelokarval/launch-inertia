"""
Launch services — config resolution with Redis caching.

Provides two config levels:
- get_page_config(): Frontend props (via to_props(), no n8n/internal keys)
- get_full_config(): Backend config (via get_resolved_config(), includes n8n)
"""

import logging
from typing import Optional

from django.core.cache import cache

from apps.launches.models import CapturePage
from apps.launches.signals import CACHE_TIMEOUT, _cache_key

logger = logging.getLogger(__name__)

# Separate cache prefix for full config (backend use)
_FULL_CACHE_PREFIX = "capture_page_full"


def _full_cache_key(slug: str) -> str:
    return f"{_FULL_CACHE_PREFIX}:{slug}"


class CapturePageService:
    """Service for retrieving capture page configs with caching."""

    @classmethod
    def get_page_config(cls, slug: str) -> Optional[dict]:
        """Get frontend props by slug, with Redis caching.

        Returns the shape expected by the Capture/Index React component.
        Does NOT include backend-only keys (n8n, etc.).
        Returns None if the slug does not exist in the database.
        Cache is invalidated via post_save/post_delete signals.
        """
        key = _cache_key(slug)
        cached = cache.get(key)
        if cached is not None:
            return cached

        try:
            page = CapturePage.objects.select_related("launch", "interest").get(
                slug=slug, is_deleted=False
            )
        except CapturePage.DoesNotExist:
            return None

        config = page.to_props()
        cache.set(key, config, timeout=CACHE_TIMEOUT)
        return config

    @classmethod
    def get_full_config(cls, slug: str) -> Optional[dict]:
        """Get the full resolved config by slug, with Redis caching.

        Returns the complete config including backend-only keys (n8n,
        launch_code, etc.). Used by views for POST handling (N8N payload,
        thank-you redirect).
        Returns None if the slug does not exist in the database.
        """
        key = _full_cache_key(slug)
        cached = cache.get(key)
        if cached is not None:
            return cached

        try:
            page = CapturePage.objects.select_related("launch", "interest").get(
                slug=slug, is_deleted=False
            )
        except CapturePage.DoesNotExist:
            return None

        config = page.get_resolved_config()

        # Inject launch_code into n8n section for N8N payload compatibility
        if page.launch_id:
            config.setdefault("n8n", {}).setdefault(
                "launch_code", page.launch.launch_code
            )

        cache.set(key, config, timeout=CACHE_TIMEOUT)
        return config

    @classmethod
    def get_page(cls, slug: str) -> Optional[CapturePage]:
        """Get the CapturePage model instance by slug."""
        try:
            return CapturePage.objects.select_related("launch", "interest").get(
                slug=slug, is_deleted=False
            )
        except CapturePage.DoesNotExist:
            return None
