"""
Cache invalidation signals for Launch config.

When a CapturePage or Launch is saved/deleted, the Redis cache for
the affected page slug is invalidated so the next request fetches
fresh data from the database.

Invalidates BOTH cache layers:
- capture_page_config:{slug} — frontend props (to_props)
- capture_page_full:{slug} — backend full config (get_resolved_config)
"""

import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.launches.models import CapturePage, Launch

logger = logging.getLogger(__name__)

CACHE_PREFIX = "capture_page_config"
FULL_CACHE_PREFIX = "capture_page_full"
MODEL_CACHE_PREFIX = "capture_page_model"
CACHE_TIMEOUT = 3600  # 1 hour


def _cache_key(slug: str) -> str:
    return f"{CACHE_PREFIX}:{slug}"


def _all_cache_keys(slug: str) -> list[str]:
    """Return all cache keys for a given slug (all layers)."""
    return [
        f"{CACHE_PREFIX}:{slug}",
        f"{FULL_CACHE_PREFIX}:{slug}",
        f"{MODEL_CACHE_PREFIX}:{slug}",
    ]


@receiver(post_save, sender=CapturePage)
def invalidate_page_cache_on_save(
    sender: type, instance: CapturePage, **kwargs: object
) -> None:
    """Invalidate cached config when a CapturePage is saved."""
    cache.delete_many(_all_cache_keys(instance.slug))
    logger.info("Cache invalidated for capture page: %s", instance.slug)


@receiver(post_delete, sender=CapturePage)
def invalidate_page_cache_on_delete(
    sender: type, instance: CapturePage, **kwargs: object
) -> None:
    """Invalidate cached config when a CapturePage is deleted."""
    cache.delete_many(_all_cache_keys(instance.slug))
    logger.info("Cache deleted for capture page: %s", instance.slug)


@receiver(post_save, sender=Launch)
def invalidate_launch_pages_cache(
    sender: type, instance: Launch, **kwargs: object
) -> None:
    """When a Launch is saved, invalidate cache for ALL its pages.

    This covers changes to Launch.default_config which affect
    every page's resolved config.
    """
    page_slugs = list(instance.pages.values_list("slug", flat=True))
    if page_slugs:
        keys = []
        for slug in page_slugs:
            keys.extend(_all_cache_keys(slug))
        cache.delete_many(keys)
        logger.info(
            "Cache invalidated for %d pages of launch %s",
            len(page_slugs),
            instance.launch_code,
        )
