"""
Tests for core.tracking — DeviceProfile, CaptureEvent, services, middleware.

Covers:
- DeviceProfile hash computation and dedup
- CaptureEvent creation and queries
- DeviceProfileService get_or_create
- TrackingService (create_event, capture sessions, bind_events_to_identity)
- VisitorMiddleware (device profiling attributes on request)
"""

import uuid

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from core.tracking.models import CaptureEvent, DeviceProfile
from core.tracking.services import DeviceProfileService, TrackingService


# ── DeviceProfile Model Tests ────────────────────────────────────────


@pytest.mark.django_db
class TestDeviceProfile:
    """Tests for DeviceProfile model."""

    def test_compute_hash_deterministic(self):
        """Same inputs produce the same hash."""
        h1 = DeviceProfile.compute_hash(
            "Chrome", "120.0.6099", "Windows", "11", "desktop"
        )
        h2 = DeviceProfile.compute_hash(
            "Chrome", "120.0.6099", "Windows", "11", "desktop"
        )
        assert h1 == h2
        assert len(h1) == 32

    def test_compute_hash_major_version_only(self):
        """Only major browser version affects hash."""
        h1 = DeviceProfile.compute_hash(
            "Chrome", "120.0.6099", "Windows", "11", "desktop"
        )
        h2 = DeviceProfile.compute_hash(
            "Chrome", "120.1.9999", "Windows", "11", "desktop"
        )
        assert h1 == h2  # Same major version = same hash

    def test_compute_hash_case_insensitive(self):
        """Hash is case-insensitive."""
        h1 = DeviceProfile.compute_hash("Chrome", "120", "Windows", "11", "Desktop")
        h2 = DeviceProfile.compute_hash("chrome", "120", "windows", "11", "desktop")
        assert h1 == h2

    def test_compute_hash_different_inputs(self):
        """Different inputs produce different hashes."""
        h1 = DeviceProfile.compute_hash("Chrome", "120", "Windows", "11", "desktop")
        h2 = DeviceProfile.compute_hash("Firefox", "120", "Windows", "11", "desktop")
        assert h1 != h2

    def test_compute_hash_empty_version(self):
        """Empty browser version handled gracefully."""
        h = DeviceProfile.compute_hash("Chrome", "", "Windows", "11", "desktop")
        assert len(h) == 32

    def test_create_profile(self):
        """Create a DeviceProfile with all fields."""
        profile = DeviceProfile.objects.create(
            profile_hash=DeviceProfile.compute_hash(
                "Chrome", "120", "Windows", "11", "desktop"
            ),
            browser_family="Chrome",
            browser_version="120",
            browser_engine="Blink",
            os_family="Windows",
            os_version="11",
            device_type="desktop",
        )
        assert profile.public_id.startswith("dpf_")
        assert str(profile) == "Chrome 120 / Windows / desktop"

    def test_unique_hash_constraint(self):
        """Duplicate profile_hash raises IntegrityError."""
        from django.db import IntegrityError

        h = DeviceProfile.compute_hash("Chrome", "120", "Windows", "11", "desktop")
        DeviceProfile.objects.create(
            profile_hash=h,
            browser_family="Chrome",
            browser_version="120",
            os_family="Windows",
            os_version="11",
            device_type="desktop",
        )
        with pytest.raises(IntegrityError):
            DeviceProfile.objects.create(
                profile_hash=h,
                browser_family="Chrome",
                browser_version="120",
                os_family="Windows",
                os_version="11",
                device_type="desktop",
            )


# ── DeviceProfileService Tests ──────────────────────────────────────


@pytest.mark.django_db
class TestDeviceProfileService:
    """Tests for DeviceProfileService."""

    def test_get_or_create_from_data_creates(self):
        """Creates a new profile from device data."""
        device_data = {
            "browser_family": "Chrome",
            "browser_version": "120.0.6099",
            "browser_engine": "Blink",
            "os_family": "Windows",
            "os_version": "11",
            "device_type": "desktop",
            "device_brand": "",
            "device_model": "",
            "is_bot": False,
            "bot_name": "",
            "bot_category": "",
        }
        profile = DeviceProfileService.get_or_create_from_data(
            device_data, ua_sample="Mozilla/5.0..."
        )
        assert profile is not None
        assert profile.browser_family == "Chrome"
        assert profile.browser_version == "120"  # Major only
        assert profile.os_family == "Windows"
        assert profile.device_type == "desktop"
        assert profile.user_agent_sample == "Mozilla/5.0..."

    def test_get_or_create_from_data_deduplicates(self):
        """Same device data returns existing profile (no duplicate)."""
        device_data = {
            "browser_family": "Safari",
            "browser_version": "17.2",
            "os_family": "iOS",
            "os_version": "17.2",
            "device_type": "smartphone",
        }
        p1 = DeviceProfileService.get_or_create_from_data(device_data)
        p2 = DeviceProfileService.get_or_create_from_data(device_data)
        assert p1.pk == p2.pk
        assert DeviceProfile.objects.count() == 1

    def test_get_or_create_from_request_no_data(self):
        """Returns None when request has no device_data."""
        rf = RequestFactory()
        request = rf.get("/")
        # No device_data attribute
        result = DeviceProfileService.get_or_create_from_request(request)
        assert result is None

    def test_get_or_create_from_request_with_data(self):
        """Creates profile from request.device_data."""
        rf = RequestFactory()
        request = rf.get("/")
        request.device_data = {
            "browser_family": "Firefox",
            "browser_version": "121.0",
            "os_family": "Linux",
            "os_version": "",
            "device_type": "desktop",
        }
        profile = DeviceProfileService.get_or_create_from_request(request)
        assert profile is not None
        assert profile.browser_family == "Firefox"


# ── CaptureEvent Model Tests ────────────────────────────────────────


@pytest.mark.django_db
class TestCaptureEvent:
    """Tests for CaptureEvent model."""

    def test_create_event(self):
        """Create a basic CaptureEvent."""
        token = uuid.uuid4()
        event = CaptureEvent.objects.create(
            event_type="page_view",
            capture_token=token,
            page_path="/inscrever-wh-rc-v3/",
            page_category="capture",
        )
        assert event.public_id.startswith("cev_")
        assert event.event_type == "page_view"
        assert event.capture_token == token
        assert event.page_category == "capture"

    def test_event_str(self):
        """String representation includes type, path, and token."""
        token = uuid.uuid4()
        event = CaptureEvent.objects.create(
            event_type="form_success",
            capture_token=token,
            page_path="/inscrever-test/",
            page_category="capture",
        )
        s = str(event)
        assert "form_success" in s
        assert "/inscrever-test/" in s

    def test_event_with_device_profile(self):
        """Event linked to DeviceProfile."""
        profile = DeviceProfile.objects.create(
            profile_hash=DeviceProfile.compute_hash(
                "Chrome", "120", "Windows", "11", "desktop"
            ),
            browser_family="Chrome",
            browser_version="120",
            os_family="Windows",
            os_version="11",
            device_type="desktop",
        )
        event = CaptureEvent.objects.create(
            event_type="page_view",
            capture_token=uuid.uuid4(),
            page_path="/",
            page_category="other",
            device_profile=profile,
        )
        assert event.device_profile == profile
        assert event.device_profile.browser_family == "Chrome"

    def test_event_choices(self):
        """Event type and page category choices are valid."""
        assert CaptureEvent.EventType.PAGE_VIEW == "page_view"
        assert CaptureEvent.EventType.FORM_SUCCESS == "form_success"
        assert CaptureEvent.PageCategory.CAPTURE == "capture"
        assert CaptureEvent.PageCategory.THANK_YOU == "thank_you"
        assert CaptureEvent.PageCategory.CHECKOUT == "checkout"

    def test_event_with_geo_and_utm(self):
        """Event stores geo_data and utm_data as JSON."""
        event = CaptureEvent.objects.create(
            event_type="page_view",
            capture_token=uuid.uuid4(),
            page_path="/",
            geo_data={"city": "Sao Paulo", "country": "BR"},
            utm_data={"utm_source": "google", "utm_medium": "cpc"},
        )
        event.refresh_from_db()
        assert event.geo_data["city"] == "Sao Paulo"
        assert event.utm_data["utm_source"] == "google"


# ── TrackingService Tests ────────────────────────────────────────────


@pytest.mark.django_db
class TestTrackingService:
    """Tests for TrackingService."""

    def setup_method(self):
        cache.clear()

    def test_generate_capture_token(self):
        """Generate unique capture tokens."""
        t1 = TrackingService.generate_capture_token()
        t2 = TrackingService.generate_capture_token()
        assert t1 != t2
        # Validate UUID format
        uuid.UUID(t1)
        uuid.UUID(t2)

    def test_create_event_basic(self):
        """Create event without request."""
        token = TrackingService.generate_capture_token()
        event = TrackingService.create_event(
            event_type="page_view",
            capture_token=token,
            page_path="/test/",
            page_category="other",
        )
        assert event.pk is not None
        assert event.event_type == "page_view"
        assert event.page_path == "/test/"

    def test_create_event_with_request(self):
        """Create event enriched from request."""
        rf = RequestFactory()
        request = rf.get("/inscrever-test/", HTTP_REFERER="https://google.com")
        request.visitor_id = "fp_abc123"
        request.fingerprint_identity = None
        request.identity = None
        request.device_profile = None
        request.client_ip = "189.1.2.3"
        request.geo_data = {"city": "SP", "country": "BR"}

        token = TrackingService.generate_capture_token()
        event = TrackingService.create_event(
            event_type="page_view",
            capture_token=token,
            page_path="/inscrever-test/",
            page_category="capture",
            request=request,
        )
        assert event.visitor_id == "fp_abc123"
        assert event.ip_address == "189.1.2.3"
        assert event.geo_data["city"] == "SP"
        assert "google.com" in event.referrer

    def test_create_event_with_extra_data(self):
        """Create event with extra metadata."""
        token = TrackingService.generate_capture_token()
        event = TrackingService.create_event(
            event_type="form_error",
            capture_token=token,
            page_path="/inscrever-test/",
            page_category="capture",
            extra_data={"errors": {"email": "Invalid"}},
        )
        assert event.extra_data["errors"]["email"] == "Invalid"

    def test_capture_session_lifecycle(self):
        """Start, get, update capture session in Redis."""
        token = TrackingService.generate_capture_token()
        TrackingService.start_capture_session(token, "wh-rc-v3")

        session = TrackingService.get_capture_session(token)
        assert session is not None
        assert session["slug"] == "wh-rc-v3"
        assert session["status"] == "viewing"

        TrackingService.update_capture_session(
            token, {"status": "converted", "email": "test@test.com"}
        )
        session = TrackingService.get_capture_session(token)
        assert session["status"] == "converted"
        assert session["email"] == "test@test.com"

    def test_capture_session_nonexistent(self):
        """Get non-existent session returns None."""
        assert TrackingService.get_capture_session("nonexistent") is None

    def test_bind_events_to_identity(self):
        """Bind anonymous events to identity after conversion."""
        token = uuid.uuid4()

        # Create anonymous events
        CaptureEvent.objects.create(
            event_type="page_view",
            capture_token=token,
            page_path="/inscrever-test/",
            page_category="capture",
        )
        CaptureEvent.objects.create(
            event_type="form_attempt",
            capture_token=token,
            page_path="/inscrever-test/",
            page_category="capture",
        )

        # Create a mock identity-like object
        from tests.factories import IdentityFactory

        identity = IdentityFactory()

        count = TrackingService.bind_events_to_identity(
            str(token), identity, visitor_id="fp_xyz"
        )
        assert count == 2

        # Verify events are now bound
        events = CaptureEvent.objects.filter(capture_token=token)
        for event in events:
            assert event.identity == identity
            assert event.visitor_id == "fp_xyz"

    def test_bind_events_skips_already_bound(self):
        """Events already bound to an identity are not re-bound."""
        from tests.factories import IdentityFactory

        token = uuid.uuid4()
        identity1 = IdentityFactory()
        identity2 = IdentityFactory()

        # Create event already bound to identity1
        CaptureEvent.objects.create(
            event_type="page_view",
            capture_token=token,
            page_path="/",
            identity=identity1,
        )

        # Try to bind to identity2 — should not change
        count = TrackingService.bind_events_to_identity(
            str(token), identity2, visitor_id="fp_new"
        )
        assert count == 0

        event = CaptureEvent.objects.get(capture_token=token)
        assert event.identity == identity1


# ── VisitorMiddleware Tests ──────────────────────────────────────────


@pytest.mark.django_db
class TestVisitorMiddleware:
    """Tests for VisitorMiddleware device profiling."""

    def test_middleware_sets_device_data(self):
        """Middleware populates request.device_data from User-Agent."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        # Use a content path (not "/") since "/" is in _SKIP_EXACT
        request = rf.get(
            "/inscrever-test/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        # Simulate session (needed for middleware chain)
        request.COOKIES = {}

        response = middleware(request)

        assert hasattr(request, "device_data")
        assert request.device_data["browser_family"] == "Chrome"
        assert request.device_data["os_family"] == "Windows"
        assert request.device_data["device_type"] == "desktop"
        assert response.status_code == 200

    def test_middleware_sets_client_hints(self):
        """Middleware reads Client Hints headers."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        # Use a content path (not "/") since "/" is in _SKIP_EXACT
        request = rf.get(
            "/inscrever-test/",
            HTTP_USER_AGENT="Mozilla/5.0",
            HTTP_SEC_CH_UA='"Chromium";v="120"',
            HTTP_SEC_CH_UA_PLATFORM='"Windows"',
            HTTP_SEC_CH_UA_MODEL='"Pixel 7"',
        )
        request.COOKIES = {}

        middleware(request)

        assert request.client_hints["platform"] == '"Windows"'
        assert request.client_hints["model"] == '"Pixel 7"'
        # Client Hints override device_data
        assert request.device_data["os_family"] == "Windows"
        assert request.device_data["device_model"] == "Pixel 7"

    def test_middleware_sets_accept_ch_header(self):
        """Response includes Accept-CH header for Client Hints."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        # Use a content path (not "/") since "/" is in _SKIP_EXACT
        request = rf.get("/inscrever-test/", HTTP_USER_AGENT="Mozilla/5.0")
        request.COOKIES = {}

        response = middleware(request)

        assert "Accept-CH" in response
        assert "Sec-CH-UA-Model" in response["Accept-CH"]

    def test_middleware_creates_device_profile(self):
        """Middleware creates DeviceProfile via dimension table."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        # Use a content path (not "/") since "/" is in _SKIP_EXACT
        request = rf.get(
            "/inscrever-test/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.2 Mobile/15E148 Safari/604.1"
            ),
        )
        request.COOKIES = {}

        middleware(request)

        assert request.device_profile is not None
        assert request.device_profile.device_type == "smartphone"
        assert DeviceProfile.objects.count() == 1

    def test_middleware_unknown_visitor(self):
        """Middleware sets visitor attributes for unknown visitor."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        request = rf.get("/", HTTP_USER_AGENT="Mozilla/5.0")
        request.COOKIES = {}

        middleware(request)

        assert request.visitor_id == ""
        assert request.fingerprint_identity is None
        assert request.identity is None
        assert request.is_known_visitor is False

    def test_middleware_geo_no_geoip_db(self):
        """Middleware handles missing GeoIP databases gracefully."""
        from core.tracking.middleware import VisitorMiddleware

        def dummy_response(request):
            from django.http import HttpResponse

            return HttpResponse("OK")

        middleware = VisitorMiddleware(dummy_response)
        rf = RequestFactory()
        request = rf.get("/", HTTP_USER_AGENT="Mozilla/5.0")
        request.COOKIES = {}

        middleware(request)

        # Should still set geo attributes (empty)
        assert hasattr(request, "client_ip")
        assert hasattr(request, "geo_data")
        assert request.geo_data == {}
