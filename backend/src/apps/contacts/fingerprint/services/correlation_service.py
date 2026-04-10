"""
Form-Fingerprint Correlation Service.

Validates that a fingerprint payload and a form payload belong to the
same visitor, extracts attribution (UTM) data, normalizes contact fields,
and produces a consolidated event dict ready for the resolution pipeline.

Ported from legacy contact/services/correlation_service.py and adapted
to use the new model architecture (Attribution, ContactEmail, ContactPhone).
"""

import logging
import re
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)


class CorrelationService:
    """
    Correlates fingerprint data with form submission data.

    Entry point: correlate()
    """

    # Known disposable email domains
    DISPOSABLE_DOMAINS = frozenset(
        {
            "10minutemail.com",
            "tempmail.org",
            "guerrillamail.com",
            "mailinator.com",
            "temp-mail.org",
            "throwaway.email",
            "yopmail.com",
            "guerrillamail.net",
            "sharklasers.com",
            "grr.la",
            "guerrillamail.info",
            "guerrillamail.de",
            "tmail.com",
            "dispostable.com",
        }
    )

    # ── Main Entry Point ──────────────────────────────────────────────

    @classmethod
    def correlate(
        cls,
        fingerprint_payload: dict[str, Any],
        form_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Correlate a fingerprint payload with a form submission payload.

        Steps:
        1. Validate visitorId match between both payloads
        2. Extract + normalize contact data (email, phone, name)
        3. Extract attribution data (UTM params, referrer, landing page)
        4. Build consolidated event dict

        Args:
            fingerprint_payload: FingerprintJS Pro webhook payload.
            form_payload: Form submission data from frontend.

        Returns:
            Consolidated event dict ready for the resolution pipeline.

        Raises:
            ValueError: If visitorId mismatch.
        """
        # 1. Validate visitorId match
        fp_visitor_id = fingerprint_payload.get("fingerprint", {}).get("visitorId")
        form_visitor_id = form_payload.get("fingerprint", {}).get("visitorId")

        if fp_visitor_id != form_visitor_id:
            raise ValueError(
                f"Fingerprint mismatch: {fp_visitor_id} != {form_visitor_id}"
            )

        # 2. Extract contact data
        form_data = form_payload.get("formData", {})
        contact_data = {
            "email": cls.normalize_email(form_data.get("email")),
            "phone": cls.normalize_phone(form_data.get("phone")),
            "name": (form_data.get("name") or "").strip(),
        }

        # 3. Extract attribution
        attribution_data = cls.extract_attribution(form_payload)

        # 4. Build consolidated event
        consolidated = {
            "visitorId": fp_visitor_id,
            "fingerprint_data": fingerprint_payload.get("fingerprint"),
            "contact_data": contact_data,
            "attribution_data": attribution_data,
            "session_data": form_payload.get("sessionData", {}),
            "device_context": form_payload.get("deviceContext", {}),
            "correlation_timestamp": timezone.now().isoformat(),
        }

        logger.info("Correlated fingerprint %s with form data", fp_visitor_id)
        return consolidated

    # ── Attribution Extraction ────────────────────────────────────────

    @staticmethod
    def extract_attribution(form_payload: dict[str, Any]) -> dict[str, Any]:
        """
        Extract marketing attribution data from form payload.

        Looks in both formData and sessionData for UTM parameters.
        """
        form_data = form_payload.get("formData", {})
        session_data = form_payload.get("sessionData", {})

        return {
            "utm_source": form_data.get("utm_source")
            or session_data.get("utm_source")
            or "",
            "utm_medium": form_data.get("utm_medium")
            or session_data.get("utm_medium")
            or "",
            "utm_campaign": form_data.get("utm_campaign")
            or session_data.get("utm_campaign")
            or "",
            "utm_content": form_data.get("utm_content")
            or session_data.get("utm_content")
            or "",
            "utm_term": form_data.get("utm_term") or session_data.get("utm_term") or "",
            "referrer": session_data.get("referrer") or "",
            "landing_page": session_data.get("pageUrl") or "",
        }

    # ── Contact Normalization ─────────────────────────────────────────

    @staticmethod
    def normalize_email(email: str | None) -> str:
        """Normalize email: lowercase, strip, validate format."""
        if not email:
            return ""
        email = email.lower().strip()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            logger.warning("Invalid email format: %s", email)
            return email  # Return as-is for debugging
        return email

    @staticmethod
    def normalize_phone(phone: str | None) -> str:
        """Normalize phone to E.164-like format."""
        if not phone:
            return ""
        # Remove everything except digits and +
        phone = re.sub(r"[^\d+]", "", phone)
        if not phone.startswith("+"):
            if phone.startswith("55"):
                phone = f"+{phone}"
            else:
                phone = f"+55{phone}"
        return phone

    # ── Contact Metadata ──────────────────────────────────────────────

    @staticmethod
    def extract_contact_metadata(form_payload: dict[str, Any]) -> dict[str, Any]:
        """Extract additional metadata from the form submission context."""
        device_context = form_payload.get("deviceContext", {})
        session_data = form_payload.get("sessionData", {})
        return {
            "form_source": session_data.get("pageUrl"),
            "user_agent": device_context.get("userAgent"),
            "screen_resolution": device_context.get("screenResolution"),
            "language": device_context.get("language"),
            "timezone": device_context.get("timezone"),
            "submission_timestamp": session_data.get("timestamp"),
        }

    # ── Validation ────────────────────────────────────────────────────

    @classmethod
    def validate_contact_data(cls, contact_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and enrich contact data.

        Returns a validation result dict with is_valid, errors, warnings,
        and enrichments.
        """
        result: dict[str, Any] = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "enrichments": {},
        }

        # Validate email
        email = contact_data.get("email")
        if email:
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(pattern, email):
                result["errors"].append("Invalid email format")
                result["is_valid"] = False
            else:
                domain = email.split("@")[1] if "@" in email else ""
                result["enrichments"]["email_domain"] = domain
                if cls.is_disposable_domain(domain):
                    result["warnings"].append("Disposable email domain detected")

        # Validate phone
        phone = contact_data.get("phone")
        if phone:
            if not re.match(r"^\+\d{10,15}$", phone):
                result["warnings"].append("Phone format may be invalid")
            else:
                if phone.startswith("+55"):
                    result["enrichments"]["phone_country"] = "BR"
                elif phone.startswith("+1"):
                    result["enrichments"]["phone_country"] = "US"

        return result

    @classmethod
    def is_disposable_domain(cls, domain: str) -> bool:
        """Check if the domain is a known disposable email provider."""
        return domain.lower() in cls.DISPOSABLE_DOMAINS

    # ── Form Quality Scoring ──────────────────────────────────────────

    @staticmethod
    def calculate_form_quality_score(form_payload: dict[str, Any]) -> float:
        """
        Calculate a quality score for the form submission (0.0 - 1.0).

        Components:
        - Email present: +0.4
        - Phone present: +0.3
        - Name present: +0.2
        - UTM source present: +0.1
        """
        score = 0.0
        form_data = form_payload.get("formData", {})

        if form_data.get("email"):
            score += 0.4
        if form_data.get("phone"):
            score += 0.3
        if form_data.get("name"):
            score += 0.2
        if form_data.get("utm_source"):
            score += 0.1

        return min(score, 1.0)

    # ── Attribution Persistence ───────────────────────────────────────

    @staticmethod
    def save_attribution(
        identity, attribution_data: dict[str, Any], touchpoint_type: str = "form"
    ):
        """
        Create an Attribution record for an identity from extracted attribution data.

        Args:
            identity: The Identity instance to attach the attribution to.
            attribution_data: Dict from extract_attribution().
            touchpoint_type: Source type (form, api, import, webhook).

        Returns:
            Attribution instance or None if no UTM data.
        """
        from apps.contacts.identity.models import Attribution

        # Only create if there's meaningful attribution data
        has_data = any(
            attribution_data.get(k)
            for k in (
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "referrer",
                "landing_page",
            )
        )

        if not has_data:
            return None

        return Attribution.objects.create(
            identity=identity,
            utm_source=attribution_data.get("utm_source", ""),
            utm_medium=attribution_data.get("utm_medium", ""),
            utm_campaign=attribution_data.get("utm_campaign", ""),
            utm_content=attribution_data.get("utm_content", ""),
            utm_term=attribution_data.get("utm_term", ""),
            referrer=attribution_data.get("referrer", ""),
            landing_page=attribution_data.get("landing_page", ""),
            touchpoint_type=touchpoint_type,
        )
