"""
CaptureService — core business logic for lead capture.

Orchestrates:
1. Server-side validation of form data
2. Identity resolution via existing ResolutionService
3. Attribution tracking via CorrelationService
4. Async N8N webhook forwarding via Celery
"""

import logging
import re
import hashlib
import time
import uuid
from typing import Any

from django.db import IntegrityError, transaction
from django.http import HttpRequest

from apps.ads.models import CaptureSubmission
from apps.ads.services.utm_parser import UTMParserService
from apps.contacts.fingerprint.services.correlation_service import (
    CorrelationService,
)
from apps.contacts.identity.models import Identity
from apps.contacts.identity.services.resolution_service import (
    ResolutionService,
)
from apps.landing.models import LeadCaptureIdempotencyKey
from apps.landing.services.n8n_proxy import N8NProxyService
from apps.landing.services.outbox import LeadIntegrationOutboxService
from core.tracking.models import CaptureEvent
from core.tracking.services import DeviceProfileService, TrackingService

logger = logging.getLogger(__name__)

# Email validation regex (RFC-like, matches legacy)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Temporary/disposable email domains to reject
_DISPOSABLE_DOMAINS = {
    "guerrillamail.com",
    "mailinator.com",
    "yopmail.com",
    "tempmail.com",
    "throwaway.email",
    "10minutemail.com",
    "guerrillamailblock.com",
    "sharklasers.com",
    "grr.la",
    "guerrillamail.info",
    "guerrillamail.de",
    "spam4.me",
    "trashmail.com",
    "fakeinbox.com",
}

# Minimum digits for a valid phone number
_PHONE_MIN_DIGITS = 7
_PHONE_MAX_DIGITS = 18


class CaptureService:
    """Lead capture business logic."""

    @staticmethod
    def build_submit_idempotency_key(
        *,
        campaign_slug: str,
        email: str,
        capture_token: str,
        request_id: str,
    ) -> str:
        """Build a deterministic idempotency key for one logical submit."""
        normalized_email = email.strip().lower()
        source = request_id.strip() or str(capture_token).strip()
        raw = f"{campaign_slug}|{source}|{normalized_email}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def _lock_submit_idempotency(
        cls,
        *,
        campaign_slug: str,
        email: str,
        capture_token: str,
        request_id: str,
        capture_page: Any = None,
    ) -> LeadCaptureIdempotencyKey:
        """Lock or create the idempotency record for one logical submit."""
        key = cls.build_submit_idempotency_key(
            campaign_slug=campaign_slug,
            email=email,
            capture_token=capture_token,
            request_id=request_id,
        )

        try:
            capture_uuid = uuid.UUID(str(capture_token))
        except (TypeError, ValueError, AttributeError):
            capture_uuid = uuid.uuid4()

        defaults = {
            "capture_token": capture_uuid,
            "request_id": request_id,
            "email_normalized": email.strip().lower(),
            "status": LeadCaptureIdempotencyKey.Status.PROCESSING,
            "capture_page": capture_page,
        }

        try:
            record, _ = LeadCaptureIdempotencyKey.objects.get_or_create(
                key=key,
                defaults=defaults,
            )
        except IntegrityError:
            record = LeadCaptureIdempotencyKey.objects.get(key=key)

        record = LeadCaptureIdempotencyKey.objects.select_for_update().get(pk=record.pk)

        update_fields: list[str] = []
        if not record.request_id and request_id:
            record.request_id = request_id
            update_fields.append("request_id")
        if record.capture_page_id is None and capture_page is not None:
            record.capture_page = capture_page
            update_fields.append("capture_page")
        if update_fields:
            record.save(update_fields=update_fields + ["updated_at"])

        return record

    @classmethod
    def validate_form_data(cls, data: dict[str, Any]) -> dict[str, str]:
        """Server-side validation of capture form data.

        Args:
            data: Form data from request.data.

        Returns:
            Dict of field_name -> error_message. Empty dict means valid.
        """
        errors: dict[str, str] = {}

        # Email validation
        email = (data.get("email") or "").strip().lower()
        if not email:
            errors["email"] = "E-mail e obrigatorio."
        elif not _EMAIL_RE.match(email):
            errors["email"] = "E-mail invalido."
        elif len(email) > 254:
            errors["email"] = "E-mail muito longo."
        else:
            domain = email.split("@")[1] if "@" in email else ""
            if domain in _DISPOSABLE_DOMAINS:
                errors["email"] = "Por favor, use um e-mail permanente."

        # Phone validation
        phone = (data.get("phone") or "").strip()
        if not phone:
            errors["phone"] = "Telefone e obrigatorio."
        else:
            digits = re.sub(r"\D", "", phone)
            if len(digits) < _PHONE_MIN_DIGITS:
                errors["phone"] = "Telefone invalido."
            elif len(digits) > _PHONE_MAX_DIGITS:
                errors["phone"] = "Telefone muito longo."

        return errors

    @classmethod
    def process_lead(
        cls,
        *,
        email: str,
        phone: str,
        visitor_id: str,
        request_id: str,
        utm_data: dict[str, str],
        campaign_config: dict[str, Any],
        page_url: str = "",
        referrer: str = "",
        session_identity: Identity | None = None,
    ) -> dict[str, Any]:
        """Process a captured lead end-to-end.

        1. Resolve identity (create or find existing)
        2. Merge session-based anonymous identity if different
        3. Save UTM attribution
        4. Build N8N payload (sent async via Celery task)

        Args:
            email: Validated email address.
            phone: Validated phone number.
            visitor_id: FingerprintJS visitorId.
            request_id: FingerprintJS requestId.
            utm_data: UTM parameters dict.
            campaign_config: Campaign JSON config.
            page_url: Full page URL for origin tracking.
            referrer: HTTP referrer.
            session_identity: Pre-existing anonymous Identity from Django
                session (created by IdentitySessionMiddleware). If present
                and different from the resolved identity, will be merged
                to preserve tracking history.

        Returns:
            Dict with resolution result and N8N payload.
        """
        # Normalize
        email = email.strip().lower()
        phone_normalized = CorrelationService.normalize_phone(phone)

        # Step 1: Resolve identity via existing system
        fingerprint_data = {"hash": visitor_id} if visitor_id else {}
        contact_data = {"email": email, "phone": phone_normalized}

        resolution_result: dict[str, Any] = {}
        identity: Identity | None = None

        if fingerprint_data.get("hash"):
            try:
                resolution_result = ResolutionService.resolve_identity_from_real_data(
                    fingerprint_data=fingerprint_data,
                    contact_data=contact_data,
                )
                identity_id = resolution_result.get("identity_id")
                if identity_id:
                    identity = Identity.objects.filter(public_id=identity_id).first()
            except Exception:
                logger.exception("Identity resolution failed for %s", email)
        else:
            # No fingerprint — still try to resolve by contact data
            try:
                resolution_result = ResolutionService.resolve_identity_from_real_data(
                    fingerprint_data={"hash": f"no-fp-{email}"},
                    contact_data=contact_data,
                )
                identity_id = resolution_result.get("identity_id")
                if identity_id:
                    identity = Identity.objects.filter(public_id=identity_id).first()
            except Exception:
                logger.exception("Identity resolution (no FP) failed for %s", email)

        # Step 1b: Merge session identity if it differs from resolved
        # The session identity is an anonymous record created on first visit.
        # If resolution found/created a different identity (by email/phone),
        # merge the session identity INTO the resolved one so that all
        # pre-form tracking events (page_views, etc.) transfer over.
        if (
            session_identity is not None
            and identity is not None
            and session_identity.pk != identity.pk
            and session_identity.status == Identity.ACTIVE
        ):
            try:
                from apps.contacts.identity.services.merge_service import MergeService

                MergeService.execute_merge(
                    source=session_identity,
                    target=identity,
                )
                logger.info(
                    "Merged session identity %s into resolved identity %s",
                    session_identity.public_id,
                    identity.public_id,
                )
            except Exception:
                logger.exception(
                    "Failed to merge session identity %s into %s",
                    session_identity.public_id,
                    identity.public_id if identity else "?",
                )

        # If resolution failed but we have a session identity, use it
        if identity is None and session_identity is not None:
            identity = session_identity
            resolution_result = {
                "identity_id": session_identity.public_id,
                "is_new": False,
                "is_anonymous": True,
                "confidence_score": session_identity.confidence_score,
            }
            logger.info(
                "Using session identity %s as fallback (resolution failed)",
                session_identity.public_id,
            )

        # Step 2: Save attribution
        if identity and utm_data:
            try:
                CorrelationService.save_attribution(
                    identity,
                    {
                        "utm_source": utm_data.get("utm_source", ""),
                        "utm_medium": utm_data.get("utm_medium", ""),
                        "utm_campaign": utm_data.get("utm_campaign", ""),
                        "utm_content": utm_data.get("utm_content", ""),
                        "utm_term": utm_data.get("utm_term", ""),
                        "referrer": referrer,
                        "landing_page": page_url,
                    },
                    touchpoint_type="capture_form",
                )
            except Exception:
                logger.exception(
                    "Attribution save failed for %s",
                    resolution_result.get("identity_id", "unknown"),
                )

        # Step 3: Build N8N payload
        n8n_payload = N8NProxyService.build_n8n_payload(
            email=email,
            phone=phone,
            visitor_id=visitor_id or "",
            request_id=request_id or "",
            utm_data=utm_data,
            campaign_config=campaign_config,
            page_url=page_url,
            referrer=referrer,
        )

        return {
            "resolution": resolution_result,
            "identity": identity,
            "identity_id": resolution_result.get("identity_id"),
            "is_new": resolution_result.get("is_new", True),
            "n8n_payload": n8n_payload,
            "n8n_webhook_url": campaign_config.get("n8n", {}).get("webhook_url", ""),
        }

    @classmethod
    def create_capture_submission(
        cls,
        *,
        identity: Any,
        email_raw: str,
        phone_raw: str,
        capture_page: Any,
        utm_data: dict[str, str],
        extra_ad_params: dict[str, str],
        capture_token: str,
        visitor_id: str,
        request: HttpRequest,
        t_start: float,
    ) -> CaptureSubmission | None:
        """Parse UTMs and create a CaptureSubmission fact record.

        Resilient: if parsing or submission creation fails, logs error
        and returns None (never blocks the redirect).
        """
        try:
            launch = getattr(capture_page, "launch", None)
            parsed = UTMParserService.parse(
                utm_data,
                extra_ad_params,
                launch=launch,
            )

            server_render_time_ms = (time.monotonic() - t_start) * 1000
            device_profile = DeviceProfileService.get_or_create_from_request(request)
            ip_address = getattr(request, "client_ip", None) or None
            geo_data = getattr(request, "geo_data", {})

            is_duplicate = False
            if launch is not None:
                is_duplicate = CaptureSubmission.objects.filter(
                    email_raw__iexact=email_raw.strip(),
                    capture_page__launch=launch,
                    is_deleted=False,
                ).exists()

            try:
                capture_token_uuid = uuid.UUID(capture_token)
            except (ValueError, AttributeError, TypeError):
                capture_token_uuid = uuid.uuid4()

            click_id = parsed.click_id or extra_ad_params.get("fbclid", "")

            submission = CaptureSubmission.objects.create(
                identity=identity,
                email_raw=email_raw,
                phone_raw=phone_raw,
                capture_page=capture_page,
                traffic_source=parsed.traffic_source,
                ad_group=parsed.ad_group,
                ad_creative=parsed.creative,
                click_id=click_id,
                visitor_id=visitor_id,
                capture_token=capture_token_uuid,
                device_profile=device_profile,
                ip_address=ip_address,
                geo_data=geo_data or {},
                n8n_status="pending",
                server_render_time_ms=server_render_time_ms,
                is_duplicate=is_duplicate,
                raw_utm_data={**utm_data, **extra_ad_params},
            )

            logger.info(
                "CaptureSubmission created: %s (email=%s, page=%s, duplicate=%s)",
                submission.public_id,
                email_raw[:20],
                capture_page.slug,
                is_duplicate,
            )
            return submission

        except Exception:
            logger.exception(
                "Failed to create CaptureSubmission (email=%s, page=%s)",
                email_raw[:20],
                getattr(capture_page, "slug", "?"),
            )
            return None

    @classmethod
    def complete_capture(
        cls,
        *,
        request: HttpRequest,
        data: dict[str, Any],
        backend_config: dict[str, Any],
        campaign_slug: str,
        capture_token: str,
        capture_page_model: Any,
        t_start: float,
    ) -> dict[str, Any]:
        """Complete a validated capture submit through a single orchestration path.

        The database-facing parts of the capture flow run inside one atomic
        transaction so identity resolution, tracking success, intent completion,
        and fact creation move together.
        """
        page_path = f"/inscrever-{campaign_slug}/"
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()
        visitor_id = data.get("visitor_id") or data.get("fingerprint") or ""
        request_id = data.get("request_id") or data.get("eventid") or ""

        utm_data: dict[str, str] = {
            "utm_source": data.get("utm_source", ""),
            "utm_medium": data.get("utm_medium", ""),
            "utm_campaign": data.get("utm_campaign", ""),
            "utm_content": data.get("utm_content", ""),
            "utm_term": data.get("utm_term", ""),
            "utm_id": data.get("utm_id", ""),
        }

        extra_ad_params: dict[str, str] = {
            "fbclid": data.get("fbclid", ""),
            "vk_ad_id": data.get("vk_ad_id", ""),
            "vk_source": data.get("vk_source", ""),
        }

        page_url = request.build_absolute_uri()
        referrer = request.META.get("HTTP_REFERER", "")
        session_identity = getattr(request, "identity", None)
        thank_you_url = backend_config.get("form", {}).get(
            "thank_you_url",
            backend_config.get("thank_you", {}).get(
                "url", f"/obrigado-{backend_config.get('slug', campaign_slug)}/"
            ),
        )
        idempotent_result: dict[str, Any] | None = None
        outbox_entries: list[Any] = []

        with transaction.atomic():
            idempotency = cls._lock_submit_idempotency(
                campaign_slug=campaign_slug,
                email=email,
                capture_token=capture_token,
                request_id=request_id,
                capture_page=capture_page_model,
            )

            if (
                idempotency.status == LeadCaptureIdempotencyKey.Status.COMPLETED
                or idempotency.capture_submission_id is not None
            ):
                identity = idempotency.identity
                submission = idempotency.capture_submission
                idempotent_result = {
                    "resolution": {},
                    "identity": identity,
                    "identity_id": getattr(identity, "public_id", ""),
                    "is_new": False,
                    "n8n_payload": {},
                    "n8n_webhook_url": "",
                    "submission": submission,
                    "outbox_entries": [],
                    "thank_you_url": idempotency.thank_you_url or thank_you_url,
                    "email": email,
                    "phone": phone,
                    "page_url": page_url,
                    "capture_token": capture_token,
                    "idempotent_replay": True,
                }
            else:
                result = cls.process_lead(
                    email=email,
                    phone=phone,
                    visitor_id=visitor_id,
                    request_id=request_id,
                    utm_data=utm_data,
                    campaign_config=backend_config,
                    page_url=page_url,
                    referrer=referrer,
                    session_identity=session_identity,
                )

                identity = result.get("identity")

                TrackingService.create_event(
                    event_type=CaptureEvent.EventType.FORM_SUCCESS,
                    capture_token=capture_token,
                    page_path=page_path,
                    page_category=CaptureEvent.PageCategory.CAPTURE,
                    request=request,
                    capture_page=capture_page_model,
                    extra_data={
                        "email_domain": email.split("@")[-1] if "@" in email else ""
                    },
                )

                if identity is not None:
                    TrackingService.bind_events_to_identity(
                        capture_token=capture_token,
                        identity=identity,
                        visitor_id=visitor_id,
                    )

                TrackingService.complete_capture_intent(
                    capture_token=capture_token,
                    identity=identity,
                    capture_page=capture_page_model,
                )

                submission = None
                if identity is not None and capture_page_model is not None:
                    submission = cls.create_capture_submission(
                        identity=identity,
                        email_raw=data.get("email", ""),
                        phone_raw=data.get("phone", ""),
                        capture_page=capture_page_model,
                        utm_data=utm_data,
                        extra_ad_params=extra_ad_params,
                        capture_token=capture_token,
                        visitor_id=visitor_id,
                        request=request,
                        t_start=t_start,
                    )

                outbox_entries = LeadIntegrationOutboxService.enqueue_for_capture(
                    capture_token=capture_token,
                    capture_submission=submission,
                    identity_public_id=getattr(identity, "public_id", ""),
                    n8n_webhook_url=result.get("n8n_webhook_url", ""),
                    n8n_payload=result.get("n8n_payload", {}),
                    email=email,
                    phone=phone,
                    page_url=page_url,
                    request=request,
                )

                idempotency.status = LeadCaptureIdempotencyKey.Status.COMPLETED
                idempotency.capture_page = capture_page_model
                idempotency.identity = identity
                idempotency.capture_submission = submission
                idempotency.thank_you_url = thank_you_url
                idempotency.save(
                    update_fields=[
                        "status",
                        "capture_page",
                        "identity",
                        "capture_submission",
                        "thank_you_url",
                        "updated_at",
                    ]
                )

        if idempotent_result is not None:
            result = idempotent_result

        identity = result.get("identity")
        TrackingService.mark_session_converted(request, email=email)

        if identity is not None and hasattr(request, "session"):
            request.session["identity_pk"] = identity.pk
            request.session["identity_id"] = identity.public_id

        TrackingService.update_capture_session(
            capture_token=capture_token,
            updates={
                "status": "converted",
                "email_domain": email.split("@")[-1] if "@" in email else "",
            },
        )

        result.update(
            {
                "identity": identity,
                "submission": submission,
                "outbox_entries": outbox_entries,
                "thank_you_url": thank_you_url,
                "email": email,
                "phone": phone,
                "page_url": page_url,
                "capture_token": capture_token,
            }
        )
        return result
