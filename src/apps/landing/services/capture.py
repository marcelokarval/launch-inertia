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
from typing import Any

from apps.contacts.fingerprint.services.correlation_service import (
    CorrelationService,
)
from apps.contacts.identity.models import Identity
from apps.contacts.identity.services.resolution_service import (
    ResolutionService,
)
from apps.landing.services.n8n_proxy import N8NProxyService

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
