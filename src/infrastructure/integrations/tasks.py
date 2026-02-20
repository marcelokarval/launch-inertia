"""
Celery tasks for external integration event delivery.

Tasks here handle async dispatch to external APIs (Meta CAPI, etc.)
so that the main request/response cycle is never blocked by third-party calls.
"""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="integrations.send_meta_conversion",
)
def send_meta_conversion(
    self: Any,
    *,
    pixel_id: str,
    access_token: str,
    test_event_code: str = "",
    event_name: str = "Lead",
    email_hash: str = "",
    phone_hash: str = "",
    event_id: str = "",
    event_source_url: str = "",
    client_ip: str = "",
    user_agent: str = "",
    fbc: str = "",
    fbp: str = "",
    external_id: str = "",
    event_time: int | None = None,
) -> bool:
    """Send a conversion event to Meta CAPI asynchronously.

    This task is dispatched after a successful capture form submission.
    Retries up to 3 times with exponential backoff (30s, 60s, 90s).

    All parameters are serializable primitives (no Django model instances).
    Hashes must be pre-computed before dispatch.

    Args:
        pixel_id: Meta Pixel ID.
        access_token: System user access token.
        test_event_code: Optional test event code for Test Events tool.
        event_name: Event name (Lead, PageView, etc.). Default "Lead".
        email_hash: SHA-256 of normalized email.
        phone_hash: SHA-256 of digits-only phone.
        event_id: Deduplication key (capture_token UUID).
        event_source_url: Full URL of the page.
        client_ip: Visitor's IP address.
        user_agent: Visitor's User-Agent header.
        fbc: _fbc cookie value.
        fbp: _fbp cookie value.
        external_id: Identity public_id.
        event_time: Unix timestamp (seconds).

    Returns:
        True if event was accepted by Meta, False otherwise.
    """
    from infrastructure.integrations.meta_capi import MetaCAPIService

    try:
        service = MetaCAPIService(
            pixel_id=pixel_id,
            access_token=access_token,
            test_event_code=test_event_code,
        )

        if event_name == "Lead":
            response = service.send_lead_event(
                email_hash=email_hash,
                phone_hash=phone_hash,
                event_id=event_id,
                event_source_url=event_source_url,
                client_ip=client_ip,
                user_agent=user_agent,
                fbc=fbc,
                fbp=fbp,
                external_id=external_id,
                event_time=event_time,
            )
        elif event_name == "PageView":
            response = service.send_page_view_event(
                event_id=event_id,
                event_source_url=event_source_url,
                client_ip=client_ip,
                user_agent=user_agent,
                fbc=fbc,
                fbp=fbp,
                external_id=external_id,
                event_time=event_time,
            )
        else:
            logger.warning("MetaCAPI task: unsupported event_name '%s'", event_name)
            return False

        if not response.success:
            logger.warning(
                "MetaCAPI task: event '%s' failed (pixel=%s, error=%s), retrying...",
                event_name,
                pixel_id,
                response.error,
            )
            raise self.retry(countdown=30 * (self.request.retries + 1))

        logger.info(
            "MetaCAPI task: event '%s' sent (pixel=%s, events_received=%d, fbtrace=%s)",
            event_name,
            pixel_id,
            response.events_received,
            response.fbtrace_id,
        )
        return True

    except self.MaxRetriesExceededError:
        logger.error(
            "MetaCAPI task: max retries exceeded for '%s' (pixel=%s, event_id=%s)",
            event_name,
            pixel_id,
            event_id,
        )
        return False

    except Exception as exc:
        logger.exception("MetaCAPI task: unexpected error for '%s'", event_name)
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
