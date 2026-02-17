"""
Launch services — config resolution with Redis caching.

Provides two config levels:
- get_page_config(): Frontend props (via to_props(), no n8n/internal keys)
- get_full_config(): Backend config (via get_resolved_config(), includes n8n)

All methods share a single DB query via _get_page_model() with Redis caching.
"""

import logging
from typing import Optional

from django.core.cache import cache

from apps.launches.models import CapturePage
from apps.launches.signals import CACHE_TIMEOUT, _cache_key

logger = logging.getLogger(__name__)

# Separate cache prefix for full config (backend use)
_FULL_CACHE_PREFIX = "capture_page_full"

# Cache prefix for model instance (shared across all methods)
_MODEL_CACHE_PREFIX = "capture_page_model"
_MODEL_CACHE_TIMEOUT = CACHE_TIMEOUT

# Sentinel for "slug not found" (distinguish from cache miss)
_NOT_FOUND = "__NOT_FOUND__"


def _full_cache_key(slug: str) -> str:
    return f"{_FULL_CACHE_PREFIX}:{slug}"


def _model_cache_key(slug: str) -> str:
    return f"{_MODEL_CACHE_PREFIX}:{slug}"


class CapturePageService:
    """Service for retrieving capture page configs with caching.

    All public methods resolve through _get_page_model() which
    executes at most ONE DB query per slug per cache cycle.
    """

    @classmethod
    def _get_page_model(cls, slug: str) -> Optional[CapturePage]:
        """Get CapturePage model instance, with Redis caching.

        Single DB query shared by get_page_config, get_full_config,
        and get_page. Caches the model PK to avoid repeated queries;
        re-fetches from DB only on cache miss.

        Returns None if slug does not exist (also cached as negative).
        """
        model_key = _model_cache_key(slug)
        cached_pk = cache.get(model_key)

        if cached_pk == _NOT_FOUND:
            return None

        if cached_pk is not None:
            # Re-hydrate from DB by PK (single indexed lookup)
            try:
                return CapturePage.objects.select_related("launch", "interest").get(
                    pk=cached_pk, is_deleted=False
                )
            except CapturePage.DoesNotExist:
                cache.delete(model_key)
                return None

        # Cache miss — query by slug
        try:
            page = CapturePage.objects.select_related("launch", "interest").get(
                slug=slug, is_deleted=False
            )
        except CapturePage.DoesNotExist:
            cache.set(model_key, _NOT_FOUND, timeout=_MODEL_CACHE_TIMEOUT)
            return None

        cache.set(model_key, page.pk, timeout=_MODEL_CACHE_TIMEOUT)
        return page

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

        page = cls._get_page_model(slug)
        if page is None:
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

        page = cls._get_page_model(slug)
        if page is None:
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
        return cls._get_page_model(slug)
