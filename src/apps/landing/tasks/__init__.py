"""Landing page Celery tasks."""

import logging
from typing import Any

from celery import shared_task

from apps.landing.services.n8n_proxy import N8NProxyService

logger = logging.getLogger(__name__)


def _update_submission_n8n_status(
    submission_id: str,
    status: str,
    response_data: dict[str, Any] | None = None,
) -> None:
    """Update CaptureSubmission.n8n_status after webhook attempt.

    Args:
        submission_id: CaptureSubmission.public_id (csb_xxx).
        status: "sent", "failed", or "skipped".
        response_data: Optional response metadata for debug/retry.
    """
    if not submission_id:
        return
    try:
        from apps.ads.models import CaptureSubmission

        updated = CaptureSubmission.objects.filter(
            public_id=submission_id,
        ).update(
            n8n_status=status,
            n8n_response=response_data or {},
        )
        if updated:
            logger.debug("CaptureSubmission %s n8n_status -> %s", submission_id, status)
    except Exception:
        logger.exception(
            "Failed to update CaptureSubmission n8n_status: %s", submission_id
        )


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
    submission_id: str = "",
) -> bool:
    """Send lead data to N8N webhook asynchronously.

    This task is fired after CaptureService.process_lead() completes
    the identity resolution. Retries up to 3 times with 30s delay.

    If submission_id is provided, updates CaptureSubmission.n8n_status
    on success ("sent") or final failure ("failed").

    Args:
        webhook_url: N8N webhook URL.
        payload: Lead data payload.
        submission_id: Optional CaptureSubmission.public_id for status tracking.
    """
    from django.utils import timezone

    try:
        success = N8NProxyService.send_to_n8n(webhook_url, payload)
        if not success:
            logger.warning(
                "N8N webhook returned failure for %s, retrying...",
                webhook_url,
            )
            raise self.retry(countdown=30 * (self.request.retries + 1))

        # Success — update submission status
        _update_submission_n8n_status(
            submission_id,
            "sent",
            {
                "sent_at": timezone.now().isoformat(),
                "attempts": self.request.retries + 1,
            },
        )
        return success

    except self.MaxRetriesExceededError:
        # Final failure after all retries
        _update_submission_n8n_status(
            submission_id,
            "failed",
            {
                "failed_at": timezone.now().isoformat(),
                "attempts": self.request.retries + 1,
                "error": "max_retries_exceeded",
            },
        )
        logger.error(
            "N8N webhook max retries exceeded for %s (submission=%s)",
            webhook_url,
            submission_id,
        )
        return False

    except Exception as exc:
        logger.exception("N8N webhook task error: %s", exc)
        raise self.retry(exc=exc)
