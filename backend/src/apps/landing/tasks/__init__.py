"""Landing page Celery tasks."""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task

from apps.landing.models import LeadIntegrationOutbox
from apps.landing.services.n8n_proxy import N8NProxyService
from apps.landing.services.outbox import LeadIntegrationOutboxMonitoringService

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


def _update_outbox_status(
    outbox_id: str,
    *,
    status: str,
    response_data: dict[str, Any] | None = None,
    last_error: str = "",
    processed: bool = False,
    next_retry_at: Any = None,
) -> None:
    """Update outbox delivery state in a single helper."""
    from django.utils import timezone

    update_kwargs: dict[str, Any] = {
        "status": status,
        "response_data": response_data or {},
        "last_error": last_error,
        "next_retry_at": next_retry_at,
    }
    if processed:
        update_kwargs["processed_at"] = timezone.now()

    LeadIntegrationOutbox.objects.filter(public_id=outbox_id).update(**update_kwargs)


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


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="landing.process_lead_integration_outbox",
)
def process_lead_integration_outbox_task(self: Any, outbox_id: str) -> bool:
    """Process one durable outbox entry for external lead integrations."""
    from django.utils import timezone
    from infrastructure.integrations.meta_capi import MetaCAPIService

    outbox = (
        LeadIntegrationOutbox.objects.select_related("capture_submission")
        .filter(public_id=outbox_id)
        .first()
    )
    if outbox is None:
        logger.warning("LeadIntegrationOutbox not found: %s", outbox_id)
        return False

    if outbox.status in (
        LeadIntegrationOutbox.Status.SENT,
        LeadIntegrationOutbox.Status.SKIPPED,
    ):
        return True

    outbox.status = LeadIntegrationOutbox.Status.PROCESSING
    outbox.attempts += 1
    outbox.last_attempt_at = timezone.now()
    outbox.last_error = ""
    outbox.next_retry_at = None
    outbox.save(
        update_fields=[
            "status",
            "attempts",
            "last_attempt_at",
            "last_error",
            "next_retry_at",
            "updated_at",
        ]
    )

    try:
        if outbox.integration_type == LeadIntegrationOutbox.IntegrationType.N8N:
            webhook_url = outbox.payload.get("webhook_url", "")
            payload = outbox.payload.get("payload", {})
            submission_id = outbox.payload.get("submission_id", "")

            if not webhook_url:
                _update_outbox_status(
                    outbox.public_id,
                    status=LeadIntegrationOutbox.Status.SKIPPED,
                    response_data={"skipped_at": timezone.now().isoformat()},
                    processed=True,
                )
                _update_submission_n8n_status(submission_id, "skipped")
                return True

            success = N8NProxyService.send_to_n8n(webhook_url, payload)
            if not success:
                raise RuntimeError("n8n delivery failed")

            response_data = {
                "sent_at": timezone.now().isoformat(),
                "attempts": outbox.attempts,
            }
            _update_outbox_status(
                outbox.public_id,
                status=LeadIntegrationOutbox.Status.SENT,
                response_data=response_data,
                processed=True,
            )
            _update_submission_n8n_status(submission_id, "sent", response_data)
            return True

        if outbox.integration_type == LeadIntegrationOutbox.IntegrationType.META_CAPI:
            payload = outbox.payload
            service = MetaCAPIService(
                pixel_id=payload.get("pixel_id", ""),
                access_token=payload.get("access_token", ""),
                test_event_code=payload.get("test_event_code", ""),
            )
            response = service.send_lead_event(
                email_hash=payload.get("email_hash", ""),
                phone_hash=payload.get("phone_hash", ""),
                event_id=payload.get("event_id", ""),
                event_source_url=payload.get("event_source_url", ""),
                client_ip=payload.get("client_ip", ""),
                user_agent=payload.get("user_agent", ""),
                fbc=payload.get("fbc", ""),
                fbp=payload.get("fbp", ""),
                external_id=payload.get("external_id", ""),
            )
            if not response.success:
                raise RuntimeError(response.error or "meta_capi delivery failed")

            _update_outbox_status(
                outbox.public_id,
                status=LeadIntegrationOutbox.Status.SENT,
                response_data={
                    "sent_at": timezone.now().isoformat(),
                    "attempts": outbox.attempts,
                    "events_received": response.events_received,
                    "fbtrace_id": response.fbtrace_id,
                },
                processed=True,
            )
            return True

        _update_outbox_status(
            outbox.public_id,
            status=LeadIntegrationOutbox.Status.SKIPPED,
            response_data={
                "skipped_at": timezone.now().isoformat(),
                "reason": f"unsupported integration_type={outbox.integration_type}",
            },
            processed=True,
        )
        return False

    except Exception as exc:
        countdown = 30 * (self.request.retries + 1)
        is_final_failure = self.request.retries >= self.max_retries

        if is_final_failure:
            _update_outbox_status(
                outbox.public_id,
                status=LeadIntegrationOutbox.Status.FAILED,
                response_data={
                    "failed_at": timezone.now().isoformat(),
                    "attempts": outbox.attempts,
                },
                last_error=str(exc),
                processed=True,
            )
            if outbox.integration_type == LeadIntegrationOutbox.IntegrationType.N8N:
                _update_submission_n8n_status(
                    outbox.payload.get("submission_id", ""),
                    "failed",
                    {
                        "failed_at": timezone.now().isoformat(),
                        "attempts": outbox.attempts,
                        "error": str(exc),
                    },
                )
            logger.error(
                "LeadIntegrationOutbox failed permanently: %s (%s)",
                outbox.public_id,
                exc,
            )
            return False

        retry_at = timezone.now() + timedelta(seconds=countdown)
        _update_outbox_status(
            outbox.public_id,
            status=LeadIntegrationOutbox.Status.PENDING,
            response_data={
                "last_failed_at": timezone.now().isoformat(),
                "attempts": outbox.attempts,
            },
            last_error=str(exc),
            next_retry_at=retry_at,
        )
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(name="landing.monitor_lead_integrations_health")
def monitor_lead_integrations_health() -> dict[str, Any]:
    """Periodic health check for lead integration delivery SLOs."""
    snapshot = LeadIntegrationOutboxMonitoringService.get_health_snapshot()
    if snapshot["healthy"]:
        logger.info(
            "LeadIntegrationOutbox healthy: failed=%s pending=%s stale_pending=%s processing=%s",
            snapshot["failed_count"],
            snapshot["pending_count"],
            snapshot["stale_pending_count"],
            snapshot["processing_count"],
        )
    else:
        logger.error(
            "LeadIntegrationOutbox unhealthy: reasons=%s failed=%s pending=%s stale_pending=%s",
            "; ".join(snapshot["reasons"]),
            snapshot["failed_count"],
            snapshot["pending_count"],
            snapshot["stale_pending_count"],
        )
    return snapshot
