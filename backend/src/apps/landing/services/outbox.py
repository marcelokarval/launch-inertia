"""Outbox service for external lead integrations."""

from __future__ import annotations

from datetime import timedelta
import os
import uuid
from typing import Any

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.landing.models import LeadIntegrationOutbox
from core.shared.hashing import hash_email, hash_phone


class LeadIntegrationOutboxService:
    """Create and dispatch durable outbox entries for capture integrations."""

    @staticmethod
    def _parse_capture_token(capture_token: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(capture_token))
        except (TypeError, ValueError, AttributeError):
            return uuid.uuid4()

    @staticmethod
    def _build_meta_payload(
        *,
        email: str,
        phone: str,
        capture_token: str,
        page_url: str,
        request: HttpRequest,
        identity_public_id: str,
    ) -> dict[str, Any] | None:
        pixel_id = os.getenv("META_PIXEL_ID", "")
        access_token = os.getenv("META_CAPI_ACCESS_TOKEN", "")
        if not pixel_id or not access_token:
            return None

        email_hash = ""
        phone_hash = ""
        if email:
            try:
                email_hash = hash_email(email)
            except ValueError:
                pass
        if phone:
            try:
                phone_hash = hash_phone(phone)
            except ValueError:
                pass

        return {
            "pixel_id": pixel_id,
            "access_token": access_token,
            "test_event_code": os.getenv("META_CAPI_TEST_EVENT_CODE", ""),
            "event_name": "Lead",
            "email_hash": email_hash,
            "phone_hash": phone_hash,
            "event_id": capture_token,
            "event_source_url": page_url,
            "client_ip": getattr(request, "client_ip", "") or "",
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "fbc": request.COOKIES.get("_fbc", ""),
            "fbp": request.COOKIES.get("_fbp", ""),
            "external_id": identity_public_id,
        }

    @classmethod
    def enqueue_for_capture(
        cls,
        *,
        capture_token: str,
        capture_submission: Any = None,
        identity_public_id: str = "",
        n8n_webhook_url: str = "",
        n8n_payload: dict[str, Any] | None = None,
        email: str = "",
        phone: str = "",
        page_url: str = "",
        request: HttpRequest,
    ) -> list[LeadIntegrationOutbox]:
        """Create outbox entries and schedule async processing after commit."""
        capture_uuid = cls._parse_capture_token(capture_token)
        created_entries: list[LeadIntegrationOutbox] = []

        if n8n_webhook_url:
            outbox, _ = LeadIntegrationOutbox.objects.update_or_create(
                capture_token=capture_uuid,
                integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
                defaults={
                    "capture_submission": capture_submission,
                    "identity_public_id": identity_public_id,
                    "status": LeadIntegrationOutbox.Status.PENDING,
                    "payload": {
                        "webhook_url": n8n_webhook_url,
                        "payload": n8n_payload or {},
                        "submission_id": getattr(capture_submission, "public_id", ""),
                    },
                    "response_data": {},
                    "last_error": "",
                    "next_retry_at": None,
                    "processed_at": None,
                },
            )
            created_entries.append(outbox)

        meta_payload = cls._build_meta_payload(
            email=email,
            phone=phone,
            capture_token=str(capture_uuid),
            page_url=page_url,
            request=request,
            identity_public_id=identity_public_id,
        )
        if meta_payload:
            outbox, _ = LeadIntegrationOutbox.objects.update_or_create(
                capture_token=capture_uuid,
                integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
                defaults={
                    "capture_submission": capture_submission,
                    "identity_public_id": identity_public_id,
                    "status": LeadIntegrationOutbox.Status.PENDING,
                    "payload": meta_payload,
                    "response_data": {},
                    "last_error": "",
                    "next_retry_at": None,
                    "processed_at": None,
                },
            )
            created_entries.append(outbox)

        if created_entries:
            entry_ids = [entry.public_id for entry in created_entries]

            def _dispatch() -> None:
                from apps.landing.tasks import process_lead_integration_outbox_task

                for entry_id in entry_ids:
                    process_lead_integration_outbox_task.delay(entry_id)

            transaction.on_commit(_dispatch)

        return created_entries


class LeadIntegrationOutboxMonitoringService:
    """Health snapshot utilities for outbox SLOs and alerting."""

    @classmethod
    def get_health_snapshot(
        cls,
        *,
        failed_threshold: int | None = None,
        pending_threshold: int | None = None,
        pending_max_age_minutes: int | None = None,
    ) -> dict[str, Any]:
        failed_threshold = failed_threshold or int(
            getattr(settings, "LEAD_OUTBOX_FAILED_THRESHOLD", 5)
        )
        pending_threshold = pending_threshold or int(
            getattr(settings, "LEAD_OUTBOX_PENDING_THRESHOLD", 10)
        )
        pending_max_age_minutes = pending_max_age_minutes or int(
            getattr(settings, "LEAD_OUTBOX_PENDING_MAX_AGE_MINUTES", 30)
        )
        n8n_slo_minutes = int(getattr(settings, "LEAD_OUTBOX_N8N_SLO_MINUTES", 10))
        meta_capi_slo_minutes = int(
            getattr(settings, "LEAD_OUTBOX_META_CAPI_SLO_MINUTES", 15)
        )

        now = timezone.now()
        pending_qs = LeadIntegrationOutbox.objects.filter(
            status=LeadIntegrationOutbox.Status.PENDING,
            is_deleted=False,
        )
        failed_qs = LeadIntegrationOutbox.objects.filter(
            status=LeadIntegrationOutbox.Status.FAILED,
            is_deleted=False,
        )

        stale_cutoff = now - timedelta(minutes=pending_max_age_minutes)
        stale_pending_qs = pending_qs.filter(created_at__lt=stale_cutoff)

        n8n_overdue_count = pending_qs.filter(
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            created_at__lt=now - timedelta(minutes=n8n_slo_minutes),
        ).count()
        meta_capi_overdue_count = pending_qs.filter(
            integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
            created_at__lt=now - timedelta(minutes=meta_capi_slo_minutes),
        ).count()

        failed_count = failed_qs.count()
        pending_count = pending_qs.count()
        stale_pending_count = stale_pending_qs.count()
        processing_count = LeadIntegrationOutbox.objects.filter(
            status=LeadIntegrationOutbox.Status.PROCESSING,
            is_deleted=False,
        ).count()

        oldest_pending = (
            pending_qs.order_by("created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        oldest_pending_age_minutes = None
        if oldest_pending is not None:
            oldest_pending_age_minutes = int(
                (now - oldest_pending).total_seconds() // 60
            )

        reasons: list[str] = []
        if failed_count >= failed_threshold:
            reasons.append(
                f"failed_count={failed_count} reached threshold={failed_threshold}"
            )
        if stale_pending_count >= pending_threshold:
            reasons.append(
                "stale_pending_count="
                f"{stale_pending_count} reached threshold={pending_threshold}"
            )
        if n8n_overdue_count > 0:
            reasons.append(
                f"n8n_overdue_count={n8n_overdue_count} breached_slo={n8n_slo_minutes}m"
            )
        if meta_capi_overdue_count > 0:
            reasons.append(
                "meta_capi_overdue_count="
                f"{meta_capi_overdue_count} breached_slo={meta_capi_slo_minutes}m"
            )

        return {
            "healthy": len(reasons) == 0,
            "failed_threshold": failed_threshold,
            "pending_threshold": pending_threshold,
            "pending_max_age_minutes": pending_max_age_minutes,
            "n8n_slo_minutes": n8n_slo_minutes,
            "meta_capi_slo_minutes": meta_capi_slo_minutes,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "processing_count": processing_count,
            "stale_pending_count": stale_pending_count,
            "n8n_overdue_count": n8n_overdue_count,
            "meta_capi_overdue_count": meta_capi_overdue_count,
            "oldest_pending_age_minutes": oldest_pending_age_minutes,
            "reasons": reasons,
            "checked_at": now.isoformat(),
        }
