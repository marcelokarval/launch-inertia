"""
VisitorMiddleware — identifies visitor and profiles device on each request.

Three responsibilities:
1. IDENTIFICATION: Reads cookie fpjs_vid, resolves FingerprintIdentity + Identity
2. DEVICE PROFILING: Parses User-Agent via device-detector, creates DeviceProfile
3. GEO: Resolves IP to location and ASN/ISP via geoip2 + django-ipware

Attributes set on request:
    Identification:
        request.visitor_id: str
        request.fingerprint_identity: FingerprintIdentity | None
        request.identity: Identity | None
        request.is_known_visitor: bool

    Device:
        request.device_profile: DeviceProfile | None
        request.device_data: dict

    Geo:
        request.client_ip: str
        request.geo_data: dict

    Client Hints:
        request.client_hints: dict
"""

import logging
from pathlib import Path
from typing import Any, cast

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse

from core.types import TrackedHttpRequest

logger = logging.getLogger(__name__)

# Cache TTLs
_VISITOR_CACHE_TTL = 3600  # 1 hour
_GEO_CACHE_TTL = 86400  # 24 hours


class VisitorMiddleware:
    """Identify visitor, profile device, resolve GeoIP on each request.

    Skip logic: Routes that are pure redirects, JSON API endpoints,
    admin, static assets, or debug toolbar are skipped entirely.
    These routes don't need device profiling or visitor identification.

    Skipped routes still get empty defaults set on request so
    downstream code (e.g., TrackingService) doesn't AttributeError.
    """

    # Prefixes where full visitor profiling is unnecessary.
    # These are either non-content routes (redirects, APIs, admin)
    # or routes served by other systems (static, DjDT).
    _SKIP_PREFIXES: tuple[str, ...] = (
        "/static/",
        "/media/",
        "/__debug__/",
        "/admin/",
        "/.well-known/",
        # Checkout JSON API endpoints (NOT the Inertia pages)
        "/checkout/create-session/",
        "/checkout/create-customer/",
        "/checkout/create-subscription/",
        "/checkout/create-payment-intent/",
        "/checkout/session-status/",
    )

    # Exact paths that are redirect-only (no content page).
    # Tracking for these happens in the view (lightweight, no device profile).
    _SKIP_EXACT: frozenset[str] = frozenset(
        {
            "/",
            "/favicon.ico",
            "/robots.txt",
            "/lembrete-bf/",
            "/recado-importante/",
            "/onboarding/",
            "/agrelliflix/",
            "/agrelliflix-aula-1/",
            "/agrelliflix-aula-2/",
            "/agrelliflix-aula-3/",
            "/agrelliflix-aula-4/",
        }
    )

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response
        self._city_reader = None
        self._asn_reader = None

    def _should_skip(self, path: str) -> bool:
        """Return True if this path should skip visitor profiling."""
        if path in self._SKIP_EXACT:
            return True
        return any(path.startswith(prefix) for prefix in self._SKIP_PREFIXES)

    def _set_empty_defaults(self, request: HttpRequest) -> None:
        """Set empty defaults on request so downstream code doesn't break."""
        req = cast(TrackedHttpRequest, request)
        req.visitor_id = ""
        req.fingerprint_identity = None
        req.identity = None
        req.is_known_visitor = False
        req._visitor_mw_identity = None
        req.device_profile = None
        req.device_data = {}
        req.client_ip = ""
        req.geo_data = {}
        req.client_hints = {}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip profiling for non-content routes
        if self._should_skip(request.path):
            self._set_empty_defaults(request)
            return self.get_response(request)

        # ─── 1. IDENTIFICATION (cookie fpjs_vid) ───
        self._identify_visitor(request)

        # ─── 2. DEVICE PROFILING (User-Agent + Client Hints) ───
        self._profile_device(request)

        # ─── 3. GEO (IP → MaxMind GeoLite2) ───
        self._resolve_geo(request)

        # ─── RESPONSE ───
        response = self.get_response(request)

        # Request high-entropy Client Hints for subsequent requests
        response["Accept-CH"] = (
            "Sec-CH-UA-Model, Sec-CH-UA-Platform-Version, "
            "Sec-CH-UA-Full-Version-List, Sec-CH-UA-Arch"
        )

        return response

    def _identify_visitor(self, request: HttpRequest) -> None:
        """Read fpjs_vid cookie and resolve to FingerprintIdentity + Identity.

        Sets request.identity for fingerprint-resolved visitors.
        Also stores identity as request._visitor_mw_identity so
        IdentitySessionMiddleware (which runs after) can detect
        divergence between session-based and fingerprint-based
        identities and flag potential merges.
        """
        req = cast(TrackedHttpRequest, request)
        visitor_id = request.COOKIES.get("fpjs_vid", "")
        req.visitor_id = visitor_id
        req.fingerprint_identity = None
        req.identity = None
        req.is_known_visitor = False
        req._visitor_mw_identity = None

        if not visitor_id:
            return

        # Try cache first
        cached = cache.get(f"visitor:{visitor_id}")
        if cached:
            try:
                self._load_cached_visitor(req, cached)
                req._visitor_mw_identity = req.identity
                return
            except Exception:
                logger.debug("Cached visitor data stale for %s", visitor_id[:8])

        # DB lookup
        try:
            from apps.contacts.fingerprint.models import FingerprintIdentity

            fp = FingerprintIdentity.objects.filter(fingerprint_hash=visitor_id).first()
            if fp:
                req.fingerprint_identity = fp
                # Resolve identity via the junction table
                identity = None
                try:
                    contact = fp.contacts.first()  # type: ignore[attr-defined]
                    if contact and hasattr(contact, "identity"):
                        identity = contact.identity
                except Exception:
                    pass

                if identity:
                    req.identity = identity

                req.is_known_visitor = True

                # Cache for subsequent requests
                cache.set(
                    f"visitor:{visitor_id}",
                    {
                        "fp_id": fp.pk,
                        "identity_id": identity.pk if identity else None,
                    },
                    timeout=_VISITOR_CACHE_TTL,
                )

            # Store fingerprint-resolved identity for IdentitySessionMiddleware
            req._visitor_mw_identity = req.identity
        except Exception:
            logger.debug("Visitor identification failed for %s", visitor_id[:8])

    def _load_cached_visitor(self, request: TrackedHttpRequest, cached: dict) -> None:
        """Load visitor from cached data."""
        from apps.contacts.fingerprint.models import FingerprintIdentity
        from apps.contacts.identity.models import Identity

        fp_id = cached.get("fp_id")
        if fp_id:
            request.fingerprint_identity = FingerprintIdentity.objects.get(pk=fp_id)
            identity_id = cached.get("identity_id")
            if identity_id:
                request.identity = Identity.objects.get(pk=identity_id)
            request.is_known_visitor = True

    def _profile_device(self, request: HttpRequest) -> None:
        """Parse User-Agent and Client Hints to build device profile.

        Resilient: if device-detector crashes (known Python 3.13
        incompatibility with lazy_regex), sets safe defaults and
        continues. Device profiling is non-critical — a request
        must never fail because of UA parsing.
        """
        from core.tracking.services import DeviceProfileService

        req = cast(TrackedHttpRequest, request)
        ua_string = request.META.get("HTTP_USER_AGENT", "")

        # device-detector 6.x has intermittent crashes on Python 3.13
        # (TypeError in lazy_regex.py, AttributeError in normalize()).
        # Wrap the entire parse in try/except to be resilient.
        try:
            from device_detector import DeviceDetector

            dd = DeviceDetector(ua_string).parse()

            # Engine extraction (device-detector v6 returns dict or str)
            engine_raw = dd.engine()
            if isinstance(engine_raw, dict):
                engine = engine_raw.get("default", "")
            else:
                engine = str(engine_raw) if engine_raw else ""

            req.device_data = {
                "browser_family": dd.client_name() or "unknown",
                "browser_version": dd.client_version() or "",
                "browser_engine": engine,
                "os_family": dd.os_name() or "unknown",
                "os_version": dd.os_version() or "",
                "device_type": dd.device_type() or "unknown",
                "device_brand": dd.device_brand() or "",
                "device_model": dd.device_model() or "",
                "is_bot": dd.is_bot(),
                "bot_name": "",
                "bot_category": "",
                "client_type": dd.client_type() or "",
            }
        except Exception:
            logger.warning("DeviceDetector parse failed for UA: %.80s", ua_string)
            req.device_data = {
                "browser_family": "unknown",
                "browser_version": "",
                "browser_engine": "",
                "os_family": "unknown",
                "os_version": "",
                "device_type": "unknown",
                "device_brand": "",
                "device_model": "",
                "is_bot": False,
                "bot_name": "",
                "bot_category": "",
                "client_type": "",
            }

        # Client Hints (Chromium only — more precise than User-Agent)
        req.client_hints = {
            "ua": request.META.get("HTTP_SEC_CH_UA", ""),
            "mobile": request.META.get("HTTP_SEC_CH_UA_MOBILE", ""),
            "platform": request.META.get("HTTP_SEC_CH_UA_PLATFORM", ""),
            "model": request.META.get("HTTP_SEC_CH_UA_MODEL", ""),
            "platform_version": request.META.get("HTTP_SEC_CH_UA_PLATFORM_VERSION", ""),
            "full_version": request.META.get("HTTP_SEC_CH_UA_FULL_VERSION_LIST", ""),
            "arch": request.META.get("HTTP_SEC_CH_UA_ARCH", ""),
        }

        # Override device_data with Client Hints when more precise
        if req.client_hints["platform"]:
            ch_platform = req.client_hints["platform"].strip('"')
            if ch_platform:
                req.device_data["os_family"] = ch_platform
        if req.client_hints["model"]:
            ch_model = req.client_hints["model"].strip('"')
            if ch_model:
                req.device_data["device_model"] = ch_model

        # DeviceProfile: get_or_create via hash (dimension table)
        try:
            req.device_profile = DeviceProfileService.get_or_create_from_request(
                request
            )
        except Exception:
            logger.debug("DeviceProfile creation failed")
            req.device_profile = None

    def _resolve_geo(self, request: HttpRequest) -> None:
        """Resolve client IP to geographic location via MaxMind GeoLite2."""
        from ipware import get_client_ip

        req = cast(TrackedHttpRequest, request)
        client_ip, is_routable = get_client_ip(request)
        req.client_ip = str(client_ip) if client_ip else ""
        req.geo_data = {}

        if not client_ip or not is_routable:
            return

        ip_str = str(client_ip)

        # Try cache first
        cached_geo = cache.get(f"geo:{ip_str}")
        if cached_geo:
            req.geo_data = cached_geo
            return

        # Check if GeoIP databases are configured and exist
        city_db = getattr(settings, "GEOIP_CITY_DB", "")
        asn_db = getattr(settings, "GEOIP_ASN_DB", "")

        if not city_db or not Path(city_db).exists():
            return

        try:
            import geoip2.database

            city_reader = geoip2.database.Reader(city_db)
            city = city_reader.city(ip_str)

            geo_data: dict[str, Any] = {
                "city": city.city.name or "",
                "country": city.country.iso_code or "",
                "country_name": city.country.name or "",
                "region": (
                    city.subdivisions.most_specific.name if city.subdivisions else ""
                ),
                "latitude": city.location.latitude,
                "longitude": city.location.longitude,
                "timezone": city.location.time_zone or "",
            }

            # ASN data (optional)
            if asn_db and Path(asn_db).exists():
                asn_reader = geoip2.database.Reader(asn_db)
                asn = asn_reader.asn(ip_str)
                geo_data["asn"] = asn.autonomous_system_number
                geo_data["isp"] = asn.autonomous_system_organization or ""

            req.geo_data = geo_data
            cache.set(f"geo:{ip_str}", geo_data, timeout=_GEO_CACHE_TTL)

        except Exception:
            # GeoIP lookup failure is non-critical
            logger.debug("GeoIP lookup failed for %s", ip_str)
