"""
Typed request protocols for the middleware stack.

Django middlewares add dynamic attributes to HttpRequest at runtime.
Pyright/Pylance cannot see these because HttpRequest's stub doesn't
declare them. This module defines typed protocols that declare all
custom attributes so that type checkers understand the enriched request.

Usage in middleware/views:
    from core.types import TrackedHttpRequest

    def my_view(request: TrackedHttpRequest) -> HttpResponse:
        # request.identity, request.device_data, etc. are all typed
        ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol, Union

from django.http import HttpRequest, QueryDict

if TYPE_CHECKING:
    from apps.contacts.fingerprint.models import FingerprintIdentity
    from apps.contacts.identity.models import Identity
    from core.tracking.models import DeviceProfile

# Type alias matching Django's set_cookie samesite parameter
SameSiteType = Literal["Lax", "Strict", "None", False] | None


class VisitorRequest(Protocol):
    """Attributes set by VisitorMiddleware.

    Provides: visitor identification, device profiling, GeoIP.
    """

    # ── Identification ──
    visitor_id: str
    """FingerprintJS visitorId from fpjs_vid cookie. Empty if no cookie."""

    fingerprint_identity: FingerprintIdentity | None
    """Resolved FingerprintIdentity from DB. None if no cookie or not found."""

    identity: Identity | None
    """Resolved Identity from fingerprint or session. None if anonymous."""

    is_known_visitor: bool
    """True if fingerprint was found in the DB."""

    _visitor_mw_identity: Identity | None
    """Internal: fingerprint-resolved Identity for IdentitySessionMiddleware
    merge detection. Not for direct use in views."""

    # ── Device ──
    device_profile: DeviceProfile | None
    """DeviceProfile dimension record. None if profiling failed."""

    device_data: dict[str, Any]
    """Parsed User-Agent data: browser_family, os_family, device_type, etc."""

    # ── Network / Geo ──
    client_ip: str
    """Client IP address from django-ipware. Empty if unresolvable."""

    geo_data: dict[str, Any]
    """GeoIP data: city, country, region, latitude, longitude, timezone, etc."""

    # ── Client Hints (Chromium) ──
    client_hints: dict[str, str]
    """Client Hints headers: ua, mobile, platform, model, etc."""


class IdentitySessionRequest(Protocol):
    """Attributes set by IdentitySessionMiddleware.

    Provides: session-based anonymous identity, visitor status.
    """

    identity: Identity | None
    """Session-based Identity. Overrides VisitorMiddleware's value."""

    visitor_status: Literal["new", "returning", "converted"]
    """Visitor lifecycle status based on session richness."""

    identity_public_id: str
    """Public ID of the session Identity. Empty if no identity."""


class InertiaDataRequest(Protocol):
    """Attributes set by InertiaJsonParserMiddleware.

    Provides: unified request.data for JSON and form-encoded bodies.
    """

    data: Union[QueryDict, dict[str, Any]]
    """Parsed request body. JSON → dict, form-encoded → QueryDict.
    ALL views MUST use request.data instead of request.POST."""


class TrackedHttpRequest(HttpRequest):
    """HttpRequest enriched by the full middleware stack.

    Declares all custom attributes from:
    - VisitorMiddleware (identification, device, geo)
    - IdentitySessionMiddleware (session identity, visitor status)
    - InertiaJsonParserMiddleware (request.data)

    Use this as the type hint for views and services that need
    access to middleware-enriched request data.
    """

    # ── VisitorMiddleware ──
    visitor_id: str
    fingerprint_identity: FingerprintIdentity | None
    identity: Identity | None
    is_known_visitor: bool
    _visitor_mw_identity: Identity | None
    device_profile: DeviceProfile | None
    device_data: dict[str, Any]
    client_ip: str
    geo_data: dict[str, Any]
    client_hints: dict[str, str]

    # ── IdentitySessionMiddleware ──
    visitor_status: Literal["new", "returning", "converted"]
    identity_public_id: str

    # ── InertiaJsonParserMiddleware ──
    data: Union[QueryDict, dict[str, Any]]  # type: ignore[assignment]
