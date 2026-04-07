"""
Tracking services — device profiling and event recording.

DeviceProfileService: Hash-based dedup for device dimension table.
TrackingService: Create CaptureEvents and manage capture sessions.
"""

import logging
import uuid
from typing import Any, Optional

from django.core.cache import cache
from django.http import HttpRequest

from core.tracking.models import CaptureEvent, CaptureIntent, DeviceProfile

logger = logging.getLogger(__name__)

# Redis TTL for capture sessions (30 minutes)
CAPTURE_SESSION_TTL = 1800


# Normalization maps for device-detector inconsistencies.
# device-detector returns "GNU/Linux" from UA parsing, but Client Hints
# send "Linux" — same OS, different names → duplicate DeviceProfiles.
# Same for "Mac" (UA) vs "macOS" (Client Hints).
_OS_NORMALIZE: dict[str, str] = {
    "gnu/linux": "GNU/Linux",
    "linux": "GNU/Linux",
    "macos": "Mac",
    "mac os x": "Mac",
    "mac": "Mac",
}

_BROWSER_NORMALIZE: dict[str, str] = {
    "chrome mobile": "Chrome Mobile",
    "mobile safari": "Mobile Safari",
    "samsung internet": "Samsung Internet",
}


def _normalize_os(os_family: str) -> str:
    """Normalize OS family name for consistent dedup hashing."""
    return _OS_NORMALIZE.get(os_family.lower().strip(), os_family)


def _normalize_browser(browser_family: str) -> str:
    """Normalize browser family name for consistent dedup hashing."""
    return _BROWSER_NORMALIZE.get(browser_family.lower().strip(), browser_family)


class DeviceProfileService:
    """Service for managing device profiles (dimension table)."""

    @classmethod
    def get_or_create_from_request(
        cls, request: HttpRequest
    ) -> Optional[DeviceProfile]:
        """Get or create a DeviceProfile from request.device_data.

        Expects VisitorMiddleware to have set request.device_data dict.
        Returns None if device_data is not available.
        """
        device_data = getattr(request, "device_data", None)
        if not device_data:
            return None

        return cls.get_or_create_from_data(
            device_data,
            ua_sample=request.META.get("HTTP_USER_AGENT", ""),
        )

    @classmethod
    def get_or_create_from_data(
        cls,
        device_data: dict[str, Any],
        ua_sample: str = "",
    ) -> DeviceProfile:
        """Get or create a DeviceProfile from parsed device data.

        Args:
            device_data: Dict with browser_family, browser_version,
                os_family, os_version, device_type, etc.
            ua_sample: Example UA string for debug.

        Returns:
            DeviceProfile instance (existing or newly created).
        """
        browser_family = _normalize_browser(
            device_data.get("browser_family", "unknown")
        )
        os_family = _normalize_os(device_data.get("os_family", "unknown"))
        browser_version = device_data.get("browser_version", "")
        os_version = device_data.get("os_version", "")
        device_type = device_data.get("device_type", "unknown")

        profile_hash = DeviceProfile.compute_hash(
            browser_family=browser_family,
            browser_version=browser_version,
            os_family=os_family,
            os_version=os_version,
            device_type=device_type,
        )

        # Major version only for storage
        major_version = browser_version.split(".")[0] if browser_version else ""

        profile, created = DeviceProfile.objects.get_or_create(
            profile_hash=profile_hash,
            defaults={
                "browser_family": browser_family,
                "browser_version": major_version,
                "browser_engine": device_data.get("browser_engine", ""),
                "os_family": os_family,
                "os_version": os_version,
                "device_type": device_type,
                "device_brand": device_data.get("device_brand", ""),
                "device_model": device_data.get("device_model", ""),
                "is_bot": device_data.get("is_bot", False),
                "bot_name": device_data.get("bot_name", ""),
                "bot_category": device_data.get("bot_category", ""),
                "user_agent_sample": ua_sample[:500] if ua_sample else "",
            },
        )

        if created:
            logger.info("New DeviceProfile created: %s (%s)", profile_hash, profile)

        return profile


class TrackingService:
    """Service for recording tracking events and managing capture sessions."""

    @classmethod
    def generate_capture_token(cls) -> str:
        """Generate a new capture_token (UUID v4) for a page load."""
        return str(uuid.uuid4())

    @classmethod
    def create_event(
        cls,
        *,
        event_type: str,
        capture_token: str,
        page_path: str,
        page_category: str = "other",
        request: Optional[HttpRequest] = None,
        capture_page: Any = None,
        extra_data: Optional[dict] = None,
    ) -> CaptureEvent:
        """Create a CaptureEvent with enriched data from the request.

        Args:
            event_type: One of CaptureEvent.EventType choices.
            capture_token: UUID linking events of the same page load.
            page_path: URL path (e.g., /inscrever-wh-rc-v3/).
            page_category: One of CaptureEvent.PageCategory choices.
            request: HttpRequest (enriched by VisitorMiddleware).
            capture_page: Optional CapturePage model instance.
            extra_data: Optional extra metadata dict.

        Returns:
            Created CaptureEvent instance.
        """
        event_kwargs: dict[str, Any] = {
            "event_type": event_type,
            "capture_token": capture_token,
            "page_path": page_path,
            "page_category": page_category,
        }

        if capture_page is not None:
            event_kwargs["capture_page"] = capture_page

        if extra_data:
            event_kwargs["extra_data"] = extra_data

        # Enrich from request if available (VisitorMiddleware attributes)
        if request is not None:
            event_kwargs["page_url"] = request.build_absolute_uri()
            event_kwargs["referrer"] = request.META.get("HTTP_REFERER", "")[:500]
            event_kwargs["accept_language"] = request.META.get(
                "HTTP_ACCEPT_LANGUAGE", ""
            )[:100]

            # Visitor identification
            event_kwargs["visitor_id"] = getattr(request, "visitor_id", "")
            event_kwargs["fingerprint_identity"] = getattr(
                request, "fingerprint_identity", None
            )
            event_kwargs["identity"] = getattr(request, "identity", None)

            # Device profile
            event_kwargs["device_profile"] = getattr(request, "device_profile", None)

            # Network
            event_kwargs["ip_address"] = getattr(request, "client_ip", "") or None
            event_kwargs["geo_data"] = getattr(request, "geo_data", {})

        event = CaptureEvent.objects.create(**event_kwargs)

        logger.debug(
            "CaptureEvent created: %s %s @ %s (token=%s)",
            event_type,
            page_category,
            page_path,
            capture_token[:8],
        )

        return event

    @classmethod
    def start_capture_session(
        cls,
        capture_token: str,
        slug: str,
        request: Optional[HttpRequest] = None,
    ) -> None:
        """Store capture session data in both Redis and Django session.

        Redis: short-lived (30min), used for dedup and event correlation.
        Django session: persistent (90-365d), used for identity tracking.

        Args:
            capture_token: The session's capture token.
            slug: Campaign/page slug.
            request: HttpRequest for extracting IP and visitor_id.
        """
        from django.utils import timezone

        now_iso = timezone.now().isoformat()
        ip = getattr(request, "client_ip", "") if request else ""
        visitor_id = getattr(request, "visitor_id", "") if request else ""

        # Redis (short-lived, event correlation)
        session_data = {
            "slug": slug,
            "started_at": now_iso,
            "ip": ip,
            "visitor_id": visitor_id,
            "status": "viewing",
        }
        cache.set(
            f"capture:session:{capture_token}",
            session_data,
            timeout=CAPTURE_SESSION_TTL,
        )

        # Django session (persistent, identity tracking)
        if request is not None and hasattr(request, "session"):
            request.session["capture_token"] = capture_token
            request.session["capture_slug"] = slug
            request.session["capture_started_at"] = now_iso
            request.session["last_page"] = f"/inscrever-{slug}/"

    @classmethod
    def get_capture_session(cls, capture_token: str) -> Optional[dict]:
        """Retrieve capture session data from Redis."""
        return cache.get(f"capture:session:{capture_token}")

    @classmethod
    def update_capture_session(
        cls,
        capture_token: str,
        updates: dict[str, Any],
    ) -> None:
        """Update capture session data in Redis.

        Merges updates into existing session data.
        """
        session_data = cls.get_capture_session(capture_token)
        if session_data is None:
            return

        session_data.update(updates)
        cache.set(
            f"capture:session:{capture_token}",
            session_data,
            timeout=CAPTURE_SESSION_TTL,
        )

    @classmethod
    def bind_events_to_identity(
        cls,
        capture_token: str,
        identity: Any,
        visitor_id: str = "",
    ) -> int:
        """Retroactively bind anonymous events to a resolved identity.

        After form_success, links all previous events with the same
        capture_token that don't have an identity yet.

        Returns:
            Number of events updated.
        """
        update_kwargs: dict[str, Any] = {"identity": identity}
        if visitor_id:
            update_kwargs["visitor_id"] = visitor_id

        count = CaptureEvent.objects.filter(
            capture_token=capture_token,
            identity__isnull=True,
        ).update(**update_kwargs)

        if count > 0:
            logger.info(
                "Bound %d anonymous events to identity %s (token=%s)",
                count,
                getattr(identity, "public_id", "?"),
                str(capture_token)[:8],
            )

        return count

    @classmethod
    def mark_session_converted(
        cls,
        request: HttpRequest,
        email: str = "",
    ) -> None:
        """Mark Django session as converted after form submission.

        Updates visitor_status to 'converted' and extends session TTL
        to 365 days. Called from the capture POST handler after
        successful identity resolution.

        Resilient: works with both real Django sessions and test
        dict-based sessions (which lack set_expiry).

        Args:
            request: HttpRequest with active session.
            email: Captured email (for session metadata).
        """
        if not hasattr(request, "session"):
            return

        try:
            request.session["visitor_status"] = "converted"
            request.session["converted_email"] = email

            # Extend session to 365 days for converted visitors
            # Real Django sessions have set_expiry; test dicts don't
            if hasattr(request.session, "set_expiry"):
                request.session.set_expiry(60 * 60 * 24 * 365)

            # Update visitor_status on request for downstream middleware
            request.visitor_status = "converted"  # type: ignore[attr-defined]

            logger.debug(
                "Session marked as converted for %s (email=%s)",
                getattr(request.session, "session_key", "?"),
                email[:20] if email else "?",
            )
        except Exception:
            logger.debug("Failed to mark session as converted")

    @classmethod
    def upsert_capture_intent(
        cls,
        *,
        request: HttpRequest,
        capture_token: str,
        email_hint: str = "",
        phone_hint: str = "",
        visitor_id: str = "",
        request_id: str = "",
    ) -> tuple[Optional[CaptureIntent], bool]:
        """Create or update a prelead CaptureIntent for a page-load session."""
        try:
            capture_uuid = uuid.UUID(str(capture_token))
        except (TypeError, ValueError, AttributeError):
            return None, False

        capture_slug = (
            request.session.get("capture_slug", "")
            if hasattr(request, "session")
            else ""
        )
        capture_page = None
        if capture_slug:
            from apps.launches.services import CapturePageService

            capture_page = CapturePageService.get_page(capture_slug)

        referer = request.META.get("HTTP_REFERER", "")
        page_path = (
            request.session.get("last_page", "/")
            if hasattr(request, "session")
            else "/"
        )
        if referer:
            from urllib.parse import urlparse

            page_path = urlparse(referer).path or page_path

        identity = getattr(request, "identity", None)
        fingerprint_identity = getattr(request, "fingerprint_identity", None)
        resolved_visitor_id = visitor_id or getattr(request, "visitor_id", "")

        intent, created = CaptureIntent.objects.get_or_create(
            capture_token=capture_uuid,
            defaults={
                "page_path": page_path,
                "capture_page": capture_page,
                "fingerprint_identity": fingerprint_identity,
                "identity": identity,
                "visitor_id": resolved_visitor_id,
                "request_id": request_id,
                "email_hint": email_hint,
                "phone_hint": phone_hint,
                "metadata": {"source": "capture-intent-beacon"},
            },
        )

        if created:
            return intent, True

        update_fields: list[str] = []

        if email_hint and intent.email_hint != email_hint:
            intent.email_hint = email_hint
            update_fields.append("email_hint")

        if phone_hint and intent.phone_hint != phone_hint:
            intent.phone_hint = phone_hint
            update_fields.append("phone_hint")

        if intent.identity_id is None and identity is not None:
            intent.identity = identity
            update_fields.append("identity")

        if intent.fingerprint_identity_id is None and fingerprint_identity is not None:
            intent.fingerprint_identity = fingerprint_identity
            update_fields.append("fingerprint_identity")

        if not intent.visitor_id and resolved_visitor_id:
            intent.visitor_id = resolved_visitor_id
            update_fields.append("visitor_id")

        if not intent.request_id and request_id:
            intent.request_id = request_id
            update_fields.append("request_id")

        if not intent.page_path and page_path:
            intent.page_path = page_path
            update_fields.append("page_path")

        if intent.capture_page_id is None and capture_page is not None:
            intent.capture_page = capture_page
            update_fields.append("capture_page")

        if update_fields:
            intent.save(update_fields=update_fields + ["updated_at"])

        return intent, False

    @classmethod
    def complete_capture_intent(
        cls,
        *,
        capture_token: str,
        identity: Any = None,
        capture_page: Any = None,
    ) -> int:
        """Mark a pending CaptureIntent as completed after a valid submit."""
        try:
            capture_uuid = uuid.UUID(str(capture_token))
        except (TypeError, ValueError, AttributeError):
            return 0

        from django.utils import timezone

        update_kwargs: dict[str, Any] = {
            "status": CaptureIntent.Status.COMPLETED,
            "completed_at": timezone.now(),
        }
        if identity is not None:
            update_kwargs["identity"] = identity
        if capture_page is not None:
            update_kwargs["capture_page"] = capture_page

        return (
            CaptureIntent.objects.filter(capture_token=capture_uuid)
            .exclude(status=CaptureIntent.Status.COMPLETED)
            .update(**update_kwargs)
        )

    @classmethod
    def extract_utm_from_request(cls, request: HttpRequest) -> dict[str, str]:
        """Extract UTM parameters from request.data or GET params."""
        data = getattr(request, "data", request.GET)
        return {
            "utm_source": data.get("utm_source", ""),
            "utm_medium": data.get("utm_medium", ""),
            "utm_campaign": data.get("utm_campaign", ""),
            "utm_content": data.get("utm_content", ""),
            "utm_term": data.get("utm_term", ""),
            "utm_id": data.get("utm_id", ""),
        }
