"""Unit tests for middleware helpers used by the private and public apps."""
# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false

import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore

from apps.identity.models import User
from core.inertia.middleware import (
    DelinquentMiddleware,
    InertiaShareMiddleware,
)
from core.tracking.middleware import VisitorMiddleware
from core.tracking.identity_middleware import IdentitySessionMiddleware
from tests.factories import UserFactory, ProfileFactory

class TestDelinquentMiddleware:
    """Tests for DelinquentMiddleware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = DelinquentMiddleware(self.get_response)

    def test_anonymous_user_passes_through(self, db):
        request = self.rf.get("/app/")
        request.user = AnonymousUser()
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_non_delinquent_user_passes(self, db):
        user = UserFactory(email="good@test.com")
        request = self.rf.get("/app/")
        request.user = user
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_delinquent_user_redirected(self, db):
        user = UserFactory(email="deli@test.com")

        request = self.rf.get("/app/")
        request.user = user

        with patch.object(
            type(user), "is_delinquent", new_callable=PropertyMock, return_value=True
        ):
            response = self.middleware(request)
        assert response.status_code == 302
        assert response.url == "/app/delinquent/"

    def test_delinquent_user_can_access_billing(self, db):
        user = UserFactory(email="deli2@test.com")

        request = self.rf.get("/app/billing/")
        request.user = user

        with patch.object(
            type(user), "is_delinquent", new_callable=PropertyMock, return_value=True
        ):
            self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_delinquent_user_can_access_logout(self, db):
        user = UserFactory(email="deli3@test.com")

        request = self.rf.get("/auth/logout/")
        request.user = user

        with patch.object(
            type(user), "is_delinquent", new_callable=PropertyMock, return_value=True
        ):
            self.middleware(request)
        self.get_response.assert_called_once_with(request)


@pytest.mark.django_db
class TestDelinquentView:
    """Tests for the standalone delinquent page."""

    def test_delinquent_route_renders_delinquent_component(self, client):
        user = UserFactory(email="delinquent-view@test.com")
        client.force_login(user)

        with patch.object(
            type(user),
            "is_delinquent",
            new_callable=PropertyMock,
            return_value=True,
        ):
            response = client.get("/app/delinquent/", HTTP_X_INERTIA="true")

        assert response.status_code == 200
        assert response["X-Inertia"] == "true"
        body = json.loads(response.content)
        assert body["component"] == "Delinquent"
        assert body["props"]["message"] is None

    def test_non_delinquent_user_is_redirected_to_dashboard(self, client):
        user = UserFactory(email="healthy-view@test.com")
        client.force_login(user)

        with patch.object(
            type(user),
            "is_delinquent",
            new_callable=PropertyMock,
            return_value=False,
        ):
            response = client.get("/app/delinquent/")

        assert response.status_code == 302
        assert response.url == "/app/"


class TestInertiaShareMiddleware:
    """Tests for InertiaShareMiddleware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = InertiaShareMiddleware(self.get_response)

    @patch("core.inertia.middleware.share")
    def test_shares_auth_data_for_authenticated_user(self, mock_share, db):
        user = UserFactory(email="shared@test.com")
        request = self.rf.get("/")
        request.user = user

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        # Verify share was called with auth, flash, app, locale
        assert "auth" in call_kwargs.kwargs
        assert "flash" in call_kwargs.kwargs
        assert "app" in call_kwargs.kwargs
        assert "locale" in call_kwargs.kwargs

    @patch("core.inertia.middleware.share")
    def test_shares_null_auth_for_anonymous(self, mock_share, db):
        request = self.rf.get("/")
        request.user = AnonymousUser()

        self.middleware(request)

        mock_share.assert_called_once()
        # Get the auth lambda and evaluate it
        call_kwargs = mock_share.call_args
        auth_func = call_kwargs.kwargs["auth"]
        auth_data = auth_func()
        assert auth_data["user"] is None

    @patch("core.inertia.middleware.share")
    def test_dashboard_route_shares_full_auth(self, mock_share, db):
        """Dashboard routes (/app/*) get full auth data with DB queries."""
        user = UserFactory(email="dash@test.com")
        request = self.rf.get("/app/dashboard/")
        request.user = user

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        auth_func = call_kwargs.kwargs["auth"]
        auth_data = auth_func()
        # Full auth includes user data from DB
        assert auth_data["user"] is not None
        assert auth_data["user"]["email"] == "dash@test.com"

    @patch("core.inertia.middleware.share")
    def test_landing_route_shares_lightweight_auth(self, mock_share, db):
        """Landing routes get lightweight shared data (no DB queries)."""
        user = UserFactory(email="landing@test.com")
        request = self.rf.get("/inscrever-wh-rc-v3/")
        request.user = user

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        auth_func = call_kwargs.kwargs["auth"]
        auth_data = auth_func()
        # Landing pages always get null auth (no DB query)
        assert auth_data["user"] is None

    @patch("core.inertia.middleware.share")
    def test_landing_route_shares_empty_flash(self, mock_share, db):
        """Landing routes get empty flash (no session access)."""
        request = self.rf.get("/suporte/")
        request.user = AnonymousUser()

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        flash_func = call_kwargs.kwargs["flash"]
        flash_data = flash_func()
        assert flash_data == {
            "success": None,
            "error": None,
            "warning": None,
            "info": None,
        }

    @patch("core.inertia.middleware.share")
    def test_auth_route_shares_full_data(self, mock_share, db):
        """Auth routes (/auth/*) get full shared data like dashboard."""
        request = self.rf.get("/auth/login/")
        request.user = AnonymousUser()

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        auth_func = call_kwargs.kwargs["auth"]
        auth_data = auth_func()
        # Auth routes use full auth lambda (anonymous → null user)
        assert auth_data["user"] is None

class TestVisitorMiddlewareSkipLogic:
    """Tests for VisitorMiddleware skip/short-circuit logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = VisitorMiddleware(self.get_response)

    def test_skip_static_prefix(self):
        """Static asset requests skip visitor profiling entirely."""
        request = self.rf.get("/static/css/main.css")
        self.middleware(request)
        self.get_response.assert_called_once_with(request)
        # Verify empty defaults were set
        assert request.visitor_id == ""
        assert request.device_profile is None
        assert request.device_data == {}
        assert request.client_ip == ""
        assert request.geo_data == {}

    def test_skip_admin_prefix(self):
        """Admin requests skip visitor profiling."""
        request = self.rf.get("/admin/")
        self.middleware(request)
        assert request.device_profile is None
        assert request.device_data == {}

    def test_skip_debug_toolbar_prefix(self):
        """DjDT requests skip visitor profiling."""
        request = self.rf.get("/__debug__/sql/")
        self.middleware(request)
        assert request.device_profile is None

    def test_skip_well_known_prefix(self):
        """Chrome DevTools .well-known probes skip profiling."""
        request = self.rf.get("/.well-known/appspecific/com.chrome.devtools.json")
        self.middleware(request)
        assert request.device_profile is None
        assert request.visitor_id == ""

    def test_skip_favicon(self):
        """favicon.ico requests skip profiling."""
        request = self.rf.get("/favicon.ico")
        self.middleware(request)
        assert request.device_profile is None

    def test_skip_checkout_json_api(self):
        """Checkout JSON API endpoints skip visitor profiling."""
        api_paths = [
            "/checkout/create-session/",
            "/checkout/create-customer/",
            "/checkout/create-subscription/",
            "/checkout/create-payment-intent/",
            "/checkout/session-status/",
        ]
        for path in api_paths:
            get_response = MagicMock(return_value=MagicMock(status_code=200))
            middleware = VisitorMiddleware(get_response)
            request = self.rf.get(path)
            middleware(request)
            assert request.device_profile is None, f"Expected skip for {path}"

    def test_skip_home_redirect(self):
        """Home page (redirect to /inscrever-*/) skips profiling."""
        request = self.rf.get("/")
        self.middleware(request)
        assert request.device_profile is None
        assert request.visitor_id == ""

    def test_skip_placeholder_redirects(self):
        """Placeholder redirect routes skip profiling."""
        placeholder_paths = [
            "/lembrete-bf/",
            "/recado-importante/",
            "/onboarding/",
            "/agrelliflix/",
            "/agrelliflix-aula-1/",
            "/agrelliflix-aula-2/",
            "/agrelliflix-aula-3/",
            "/agrelliflix-aula-4/",
        ]
        for path in placeholder_paths:
            get_response = MagicMock(return_value=MagicMock(status_code=200))
            middleware = VisitorMiddleware(get_response)
            request = self.rf.get(path)
            middleware(request)
            assert request.device_profile is None, f"Expected skip for {path}"
            assert request.visitor_id == "", f"Expected empty visitor_id for {path}"

    @patch("core.tracking.middleware.VisitorMiddleware._profile_device")
    @patch("core.tracking.middleware.VisitorMiddleware._identify_visitor")
    @patch("core.tracking.middleware.VisitorMiddleware._resolve_geo")
    def test_content_pages_run_full_profiling(
        self, mock_geo, mock_identify, mock_profile
    ):
        """Content pages (capture, support, terms, etc.) run full profiling."""
        content_paths = [
            "/inscrever-wh-rc-v3/",
            "/obrigado-wh-rc-v3/",
            "/suporte/",
            "/suporte-launch/",
            "/terms-of-service/",
            "/privacy-policy/",
            "/checkout-wh/",
        ]
        for path in content_paths:
            mock_identify.reset_mock()
            mock_profile.reset_mock()
            mock_geo.reset_mock()
            get_response = MagicMock(return_value=MagicMock(status_code=200))
            middleware = VisitorMiddleware(get_response)
            request = self.rf.get(path)
            middleware(request)
            mock_identify.assert_called_once_with(request)
            mock_profile.assert_called_once_with(request)
            mock_geo.assert_called_once_with(request)

    def test_skipped_routes_still_have_all_attributes(self):
        """Skipped routes have all expected attributes (no AttributeError)."""
        request = self.rf.get("/admin/login/")
        self.middleware(request)
        # All attributes that downstream code might access
        assert hasattr(request, "visitor_id")
        assert hasattr(request, "fingerprint_identity")
        assert hasattr(request, "identity")
        assert hasattr(request, "is_known_visitor")
        assert hasattr(request, "device_profile")
        assert hasattr(request, "device_data")
        assert hasattr(request, "client_ip")
        assert hasattr(request, "geo_data")
        assert hasattr(request, "client_hints")

    def test_visitor_mw_identity_set_on_skipped(self):
        """Skipped routes also set _visitor_mw_identity to None."""
        request = self.rf.get("/static/main.js")
        self.middleware(request)
        assert hasattr(request, "_visitor_mw_identity")
        assert request._visitor_mw_identity is None


class TestIdentitySessionMiddleware:
    """Tests for IdentitySessionMiddleware — session-based anonymous identity."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = IdentitySessionMiddleware(self.get_response)

    def _make_request(self, path: str) -> MagicMock:
        """Create a request with a real Django session."""
        request = self.rf.get(path)
        request.session = SessionStore()
        # IdentitySessionMiddleware expects these from VisitorMiddleware
        request.identity = None
        request.visitor_status = "new"
        request.identity_public_id = ""
        request._visitor_mw_identity = None
        request.client_ip = "1.2.3.4"
        return request  # type: ignore[return-value]

    def test_skip_non_content_routes(self):
        """Non-content routes (static, admin) are skipped entirely."""
        skip_paths = [
            "/static/main.js",
            "/admin/login/",
            "/media/photo.jpg",
            "/__debug__/sql/",
        ]
        for path in skip_paths:
            request = self._make_request(path)
            self.middleware(request)
            # Should pass through without creating identity
            assert request.identity is None, f"Expected skip for {path}"
            assert request.visitor_status == "new"

    def test_first_visit_creates_anonymous_identity(self, db):
        """First visit to capture page creates anonymous Identity."""
        request = self._make_request("/inscrever-wh-rc-v3/")
        self.middleware(request)

        # Identity should be created and stored on request
        assert request.identity is not None
        assert request.identity.status == "active"
        assert request.identity.first_seen_source == "session"
        assert request.identity.confidence_score == 0.05

        # Session should have identity data
        assert request.session.get("identity_pk") == request.identity.pk
        assert request.session.get("identity_id") == request.identity.public_id
        assert request.session.get("visitor_status") == "new"
        assert request.session.get("first_seen") is not None

    def test_return_visit_recovers_identity(self, db):
        """Return visit recovers Identity from session (no new creation)."""
        from apps.contacts.identity.models import Identity

        # Create identity (simulating first visit)
        identity = Identity.objects.create(
            status=Identity.ACTIVE,
            first_seen_source="session",
            confidence_score=0.05,
        )

        # Set up session as if first visit already happened
        request = self._make_request("/inscrever-wh-rc-v3/")
        request.session["identity_pk"] = identity.pk
        request.session["identity_id"] = identity.public_id
        request.session["visitor_status"] = "new"
        request.session.save()

        self.middleware(request)

        # Should recover the same identity
        assert request.identity is not None
        assert request.identity.pk == identity.pk
        # Visitor status should be upgraded to returning
        assert request.visitor_status == "returning"
        assert request.session.get("visitor_status") == "returning"

    def test_stale_session_creates_new_identity(self, db):
        """If session identity was deleted, creates a fresh one."""
        request = self._make_request("/inscrever-wh-rc-v3/")
        # Set stale identity PK that doesn't exist in DB
        request.session["identity_pk"] = 99999
        request.session["identity_id"] = "idt_stale123"
        request.session["visitor_status"] = "returning"
        request.session.save()

        self.middleware(request)

        # Should create a new identity since the old one doesn't exist
        assert request.identity is not None
        assert request.identity.public_id != "idt_stale123"
        assert request.session.get("identity_pk") == request.identity.pk

    def test_cookies_set_on_response(self, db):
        """Response sets _lid and _vs cookies."""
        request = self._make_request("/inscrever-wh-rc-v3/")
        response = MagicMock(status_code=200)
        self.get_response.return_value = response

        self.middleware(request)

        # Check that set_cookie was called for _lid and _vs
        cookie_names = [call.args[0] for call in response.set_cookie.call_args_list]
        assert "_lid" in cookie_names
        assert "_vs" in cookie_names

        # Verify _lid value is the identity public_id
        lid_call = next(
            c for c in response.set_cookie.call_args_list if c.args[0] == "_lid"
        )
        assert lid_call.args[1] == request.identity.public_id

    def test_dashboard_routes_also_get_identity(self, db):
        """Dashboard routes (/app/*) also get identity session."""
        request = self._make_request("/app/dashboard/")
        self.middleware(request)

        assert request.identity is not None
        assert request.session.get("identity_pk") is not None

    def test_home_route_gets_identity(self, db):
        """Home route (/) also gets identity session."""
        request = self._make_request("/")
        self.middleware(request)

        assert request.identity is not None

    def test_thank_you_route_gets_identity(self, db):
        """Thank you pages get identity session."""
        request = self._make_request("/obrigado-wh-rc-v3/")
        self.middleware(request)

        assert request.identity is not None

    def test_last_page_tracked_in_session(self, db):
        """Session stores last_page on each visit."""
        request = self._make_request("/inscrever-wh-rc-v3/")
        self.middleware(request)

        assert request.session.get("last_page") == "/inscrever-wh-rc-v3/"

    def test_identity_history_created(self, db):
        """Anonymous identity creation is recorded in IdentityHistory."""
        from apps.contacts.identity.models import IdentityHistory

        request = self._make_request("/inscrever-wh-rc-v3/")
        self.middleware(request)

        history = IdentityHistory.objects.filter(
            identity=request.identity,
            operation_type=IdentityHistory.UPDATE,
        ).first()
        assert history is not None
        assert (
            history.details.get("action") == "anonymous_identity_created_from_session"
        )

    def test_request_attributes_always_set(self, db):
        """All expected request attributes exist after middleware runs."""
        # Even for skipped routes
        request = self._make_request("/static/main.css")
        self.middleware(request)

        assert hasattr(request, "identity")
        assert hasattr(request, "visitor_status")
        assert hasattr(request, "identity_public_id")

    def test_identity_public_id_on_request(self, db):
        """request.identity_public_id is set correctly."""
        request = self._make_request("/inscrever-wh-rc-v3/")
        self.middleware(request)

        assert request.identity_public_id != ""
        assert request.identity_public_id == request.identity.public_id
