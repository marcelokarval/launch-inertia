"""
Unit tests for middleware: SetupStatusMiddleware, DelinquentMiddleware,
InertiaShareMiddleware, VisitorMiddleware.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from apps.identity.models import User
from core.inertia.middleware import (
    SetupStatusMiddleware,
    DelinquentMiddleware,
    InertiaShareMiddleware,
)
from core.tracking.middleware import VisitorMiddleware
from tests.factories import UserFactory, ProfileFactory


class TestSetupStatusMiddleware:
    """Tests for SetupStatusMiddleware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = SetupStatusMiddleware(self.get_response)

    def test_anonymous_user_passes_through(self, db):
        request = self.rf.get("/app/")
        request.user = AnonymousUser()
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_staff_user_passes_through(self, db):
        user = UserFactory(email="staff@test.com", staff=True, incomplete_setup=True)
        request = self.rf.get("/app/")
        request.user = user
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_exempt_paths_pass_through(self, db):
        user = UserFactory(email="exempt@test.com", incomplete_setup=True)
        for path in ["/static/css/", "/auth/login/", "/onboarding/verify/", "/admin/"]:
            request = self.rf.get(path)
            request.user = user
            self.middleware(request)
        assert self.get_response.call_count == 4

    @patch("apps.identity.services.SetupStatusService")
    def test_complete_user_passes_through(self, mock_service_cls, db):
        user = UserFactory(email="complete@test.com", setup_status="complete")
        mock_status = MagicMock()
        mock_status.is_complete = True
        mock_status.redirect_url = "/app/"
        mock_service_cls.get_setup_status.return_value = mock_status

        request = self.rf.get("/app/")
        request.user = user
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    @patch("apps.identity.services.SetupStatusService")
    def test_incomplete_user_redirected(self, mock_service_cls, db):
        user = UserFactory(email="incomplete@test.com", incomplete_setup=True)
        mock_status = MagicMock()
        mock_status.is_complete = False
        mock_status.redirect_url = "/onboarding/verify-email/"
        mock_service_cls.get_setup_status.return_value = mock_status

        request = self.rf.get("/app/")
        request.user = user

        response = self.middleware(request)
        assert response.status_code == 302
        assert response.url == "/onboarding/verify-email/"


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

    @patch("core.inertia.middleware.share")
    def test_onboarding_route_shares_full_data(self, mock_share, db):
        """Onboarding routes (/onboarding/*) get full shared data."""
        user = UserFactory(email="onboard@test.com")
        request = self.rf.get("/onboarding/verify-email/")
        request.user = user

        self.middleware(request)

        mock_share.assert_called_once()
        call_kwargs = mock_share.call_args
        auth_func = call_kwargs.kwargs["auth"]
        auth_data = auth_func()
        assert auth_data["user"] is not None
        assert auth_data["user"]["email"] == "onboard@test.com"


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
