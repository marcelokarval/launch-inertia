"""
IdentitySessionMiddleware — session-based anonymous identity for all visitors.

Creates and persists an Identity from the first page load, using the
Django session as the persistence backbone. Every visitor gets an Identity
immediately — no form submission required.

Flow:
    1. First visit: session created → anonymous Identity created → stored in session
    2. Return visit: session loaded → Identity recovered instantly from session
    3. FingerprintJS resolves: visitor_id linked to existing Identity
    4. Form submitted: Identity enriched with email/phone (or merged)

Cookies set on response:
    _lid (non-httponly): Identity public_id — JS can read immediately
    _vs  (non-httponly): Visitor status (new/returning/converted)

Session keys:
    identity_id: Identity public_id
    identity_pk: Identity PK (for fast DB lookup)
    visitor_status: new | returning | converted
    first_seen: ISO timestamp of first visit
    last_page: last page path visited

Must run AFTER SessionMiddleware and AFTER VisitorMiddleware.
Must run BEFORE InertiaMiddleware.

Attributes set on request:
    request.identity: Identity | None
    request.visitor_status: str ("new" | "returning" | "converted")
    request.identity_public_id: str | ""
"""

import logging
from typing import Any, Literal, cast

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from core.types import SameSiteType, TrackedHttpRequest

logger = logging.getLogger(__name__)

# Cookie config
_LID_COOKIE_NAME = "_lid"  # Identity public_id (JS-readable)
_VS_COOKIE_NAME = "_vs"  # Visitor status (JS-readable)

# Session TTLs by identity richness (seconds)
_TTL_ANONYMOUS = 60 * 60 * 24 * 90  # 90 days — session only
_TTL_FINGERPRINTED = 60 * 60 * 24 * 180  # 180 days — has visitor_id
_TTL_CONVERTED = 60 * 60 * 24 * 365  # 365 days — has email/phone

# Routes that should create/load identity session.
# Non-content routes (static, admin, debug, JSON APIs) are skipped.
_LANDING_PREFIXES = (
    "/inscrever-",
    "/obrigado-",
    "/checkout-",
    "/suporte",
    "/terms-of-service/",
    "/privacy-policy/",
    "/insc-base/",
    "/lista-de-espera/",
)

# Dashboard routes also get identity session (for authenticated users)
_DASHBOARD_PREFIXES = (
    "/app/",
    "/auth/",
    "/onboarding/",
)


class IdentitySessionMiddleware:
    """Create/recover anonymous Identity via Django session.

    On first visit to a content page, creates an anonymous Identity
    and stores it in the session. On return visits, recovers the
    Identity from the session instantly (zero DB queries on cache hit).

    Sets cookies _lid and _vs on the response for frontend consumption.
    Adjusts session TTL based on identity richness.
    """

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def _should_process(self, path: str) -> bool:
        """Return True if this path should get identity session."""
        if path == "/":
            return True
        for prefix in _LANDING_PREFIXES:
            if path.startswith(prefix):
                return True
        for prefix in _DASHBOARD_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def __call__(self, request: HttpRequest) -> HttpResponse:
        req = cast(TrackedHttpRequest, request)

        # Set defaults (downstream code expects these)
        req.identity = getattr(request, "identity", None)
        req.visitor_status = "new"
        req.identity_public_id = ""

        if not self._should_process(request.path):
            return self.get_response(request)

        # ── Recover or create Identity from session ───────────────
        session = request.session
        identity = None
        identity_public_id = session.get("identity_id", "")

        if identity_public_id:
            # Return visit: recover from session
            identity = self._recover_identity(session)
            if identity:
                req.visitor_status = session.get("visitor_status", "returning")
                if req.visitor_status == "new":
                    req.visitor_status = "returning"
                    session["visitor_status"] = "returning"
            else:
                # Identity was in session but gone from DB (deleted/merged)
                # Clear stale session data and create fresh
                self._clear_identity_session(session)
                identity_public_id = ""

        if not identity_public_id:
            # First visit: create anonymous Identity
            identity = self._create_anonymous_identity(request, session)

        # ── Set on request ────────────────────────────────────────
        if identity:
            req.identity = identity
            req.identity_public_id = identity.public_id

            # Merge with VisitorMiddleware identity if available
            visitor_identity = getattr(request, "_visitor_mw_identity", None)
            if visitor_identity and visitor_identity.pk != identity.pk:
                # VisitorMiddleware found a different identity via fingerprint
                # The fingerprint-based identity should be merged later
                # For now, session identity takes precedence
                logger.debug(
                    "Session identity %s differs from visitor identity %s",
                    identity.public_id,
                    visitor_identity.public_id,
                )

        # ── Track last page ───────────────────────────────────────
        session["last_page"] = request.path

        # ── Response: set cookies ─────────────────────────────────
        response = self.get_response(request)

        if identity:
            self._set_identity_cookies(
                response,
                identity.public_id,
                req.visitor_status,
            )
            self._adjust_session_ttl(request, identity)

        return response

    def _recover_identity(self, session) -> Any:
        """Recover Identity from session data. Returns None if not found."""
        identity_pk = session.get("identity_pk")
        if not identity_pk:
            return None

        try:
            from apps.contacts.identity.models import Identity

            identity = Identity.objects.get(
                pk=identity_pk, status=Identity.ACTIVE, is_deleted=False
            )
            identity.last_seen = timezone.now()
            identity.save(update_fields=["last_seen", "updated_at"])
            return identity
        except Exception:
            logger.debug("Failed to recover identity PK=%s from session", identity_pk)
            return None

    def _create_anonymous_identity(self, request: HttpRequest, session) -> Any:
        """Create a new anonymous Identity and store in session."""
        try:
            from apps.contacts.identity.models import Identity, IdentityHistory

            identity = Identity.objects.create(
                status=Identity.ACTIVE,
                first_seen_source="session",
                last_seen=timezone.now(),
                confidence_score=0.05,  # Minimal: session-only
            )

            IdentityHistory.objects.create(
                identity=identity,
                operation_type=IdentityHistory.UPDATE,
                details={
                    "action": "anonymous_identity_created_from_session",
                    "session_key": session.session_key or "pending",
                    "path": request.path,
                    "ip": getattr(request, "client_ip", ""),
                },
            )

            # Store in session
            session["identity_id"] = identity.public_id
            session["identity_pk"] = identity.pk
            session["visitor_status"] = "new"
            session["first_seen"] = timezone.now().isoformat()

            logger.info(
                "Created session-based anonymous identity %s for %s",
                identity.public_id,
                request.path,
            )
            return identity

        except Exception:
            logger.exception("Failed to create anonymous identity from session")
            return None

    def _clear_identity_session(self, session) -> None:
        """Remove stale identity data from session."""
        for key in ("identity_id", "identity_pk", "visitor_status", "first_seen"):
            session.pop(key, None)

    def _set_identity_cookies(
        self,
        response: HttpResponse,
        identity_public_id: str,
        visitor_status: str,
    ) -> None:
        """Set _lid and _vs cookies on the response."""
        # Determine cookie age based on visitor status
        if visitor_status == "converted":
            max_age = _TTL_CONVERTED
        else:
            max_age = _TTL_ANONYMOUS

        secure: bool = getattr(settings, "SESSION_COOKIE_SECURE", False)
        samesite = cast(
            SameSiteType, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
        )

        response.set_cookie(
            _LID_COOKIE_NAME,
            identity_public_id,
            max_age=max_age,
            httponly=False,  # JS needs to read this
            secure=secure,
            samesite=samesite,
            path="/",
        )
        response.set_cookie(
            _VS_COOKIE_NAME,
            visitor_status,
            max_age=max_age,
            httponly=False,  # JS needs to read this
            secure=secure,
            samesite=samesite,
            path="/",
        )

    def _adjust_session_ttl(self, request: HttpRequest, identity: Any) -> None:
        """Extend session TTL based on identity richness.

        - Session-only (anonymous): 90 days (default)
        - Has visitor_id (fingerprint linked): 180 days
        - Has email or phone (converted): 365 days
        """
        visitor_id = getattr(request, "visitor_id", "")
        visitor_status = getattr(request, "visitor_status", "new")

        if visitor_status == "converted":
            request.session.set_expiry(_TTL_CONVERTED)
        elif visitor_id:
            request.session.set_expiry(_TTL_FINGERPRINTED)
        # Default (anonymous) uses SESSION_COOKIE_AGE = 90 days
