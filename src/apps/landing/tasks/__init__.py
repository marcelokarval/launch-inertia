"""Landing page Celery tasks."""

import logging
from typing import Any

from celery import shared_task

from apps.landing.services.n8n_proxy import N8NProxyService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="landing.send_to_n8n",
)
def send_to_n8n_task(
    self: Any,
    webhook_url: str,
    payload: dict[str, Any],
) -> bool:
    """Send lead data to N8N webhook asynchronously.

    This task is fired after CaptureService.process_lead() completes
    the identity resolution. Retries up to 3 times with 30s delay.
    """
    try:
        success = N8NProxyService.send_to_n8n(webhook_url, payload)
        if not success:
            logger.warning(
                "N8N webhook returned failure for %s, retrying...",
                webhook_url,
            )
            raise self.retry(countdown=30 * (self.request.retries + 1))
        return success
    except Exception as exc:
        logger.exception("N8N webhook task error: %s", exc)
        raise self.retry(exc=exc)
