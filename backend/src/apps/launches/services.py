"""
Launch services — config resolution with Redis caching.

Provides two config levels:
- get_page_config(): Frontend props (via to_props(), no n8n/internal keys)
- get_full_config(): Backend config (via get_resolved_config(), includes n8n)

All methods share a single DB query via _get_page_model() with Redis caching.
"""

import hashlib
import logging
from typing import Any, Optional

from django.core.cache import cache
from django.db import transaction

from apps.launches.models import CapturePage, Interest, Launch
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

    @staticmethod
    def _build_legacy_launch_code(slug: str) -> str:
        """Build a deterministic synthetic launch code for legacy JSON pages."""
        digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:10].upper()
        return f"LEG{digest}"

    @classmethod
    def _get_or_restore_legacy_launch(cls, slug: str, config: dict[str, Any]) -> Launch:
        """Get or create a Launch record for a legacy JSON-backed page."""
        n8n_config = config.get("n8n") or {}
        launch_code = str(n8n_config.get("launch_code") or "").strip()
        if not launch_code:
            launch_code = cls._build_legacy_launch_code(slug)

        launch = (
            Launch.all_objects.select_for_update()
            .filter(launch_code=launch_code)
            .first()
        )
        if launch is not None:
            if launch.is_deleted:
                launch.is_deleted = False
                launch.deleted_at = None
                launch.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
            return launch

        return Launch.objects.create(
            name=f"Legacy Launch {launch_code}"[:200],
            launch_code=launch_code,
            status=Launch.Status.DRAFT,
            default_config={},
            metadata={
                "materialized_from": "landing_json_fallback",
                "source_slug": slug,
            },
        )

    @staticmethod
    def _infer_interest_for_slug(slug: str) -> Optional[Interest]:
        """Best-effort interest resolution from slug tokens."""
        tokens = [token for token in slug.split("-") if token]
        if not tokens:
            return None

        return Interest.objects.filter(slug__in=tokens).order_by("created_at").first()

    @classmethod
    @transaction.atomic
    def materialize_legacy_page(cls, slug: str, config: dict[str, Any]) -> CapturePage:
        """Persist a legacy JSON campaign as a CapturePage for downstream facts.

        This is used during the migration period so successful submits from
        JSON-backed landings can still create a `CaptureSubmission`, which
        requires a concrete `CapturePage` foreign key.
        """
        page = cls._get_page_model(slug)
        if page is not None:
            return page

        page_config = dict(config)
        n8n_config = page_config.get("n8n") or {}
        interest = cls._infer_interest_for_slug(slug)
        page_name = str(page_config.get("meta", {}).get("title") or slug).strip()[:200]

        existing_page = (
            CapturePage.all_objects.select_related("launch", "interest")
            .select_for_update()
            .filter(slug=slug)
            .first()
        )

        if existing_page is not None:
            update_fields: list[str] = []
            if existing_page.is_deleted:
                existing_page.is_deleted = False
                existing_page.deleted_at = None
                update_fields.extend(["is_deleted", "deleted_at"])

            if existing_page.launch.is_deleted:
                existing_page.launch.is_deleted = False
                existing_page.launch.deleted_at = None
                existing_page.launch.save(
                    update_fields=["is_deleted", "deleted_at", "updated_at"]
                )

            if existing_page.name != page_name:
                existing_page.name = page_name
                update_fields.append("name")

            if existing_page.config != page_config:
                existing_page.config = page_config
                update_fields.append("config")

            webhook_url = str(n8n_config.get("webhook_url") or "")
            if existing_page.n8n_webhook_url != webhook_url:
                existing_page.n8n_webhook_url = webhook_url
                update_fields.append("n8n_webhook_url")

            list_id = str(n8n_config.get("list_id") or "")
            if existing_page.n8n_list_id != list_id:
                existing_page.n8n_list_id = list_id
                update_fields.append("n8n_list_id")

            if existing_page.interest_id is None and interest is not None:
                existing_page.interest = interest
                update_fields.append("interest")

            if update_fields:
                existing_page.save(update_fields=update_fields + ["updated_at"])

            return existing_page

        launch = cls._get_or_restore_legacy_launch(slug, page_config)

        return CapturePage.objects.create(
            launch=launch,
            interest=interest,
            slug=slug,
            name=page_name or slug,
            page_type=CapturePage.PageType.CAPTURE,
            layout_type=CapturePage.LayoutType.STANDARD,
            config=page_config,
            n8n_webhook_url=str(n8n_config.get("webhook_url") or ""),
            n8n_list_id=str(n8n_config.get("list_id") or ""),
            metadata={
                "materialized_from": "landing_json_fallback",
                "source_slug": slug,
            },
        )
