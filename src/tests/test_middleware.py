"""
Unit tests for middleware: SetupStatusMiddleware, DelinquentMiddleware, InertiaShareMiddleware.
"""

import pytest
from unittest.mock import MagicMock, patch
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

from core.inertia.middleware import (
    SetupStatusMiddleware,
    DelinquentMiddleware,
    InertiaShareMiddleware,
)
from tests.factories import UserFactory


class TestSetupStatusMiddleware:
    """Tests for SetupStatusMiddleware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=MagicMock(status_code=200))
        self.middleware = SetupStatusMiddleware(self.get_response)

    def test_anonymous_user_passes_through(self, db):
        request = self.rf.get("/dashboard/")
        request.user = AnonymousUser()
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_staff_user_passes_through(self, db):
        user = UserFactory(email="staff@test.com", staff=True, incomplete_setup=True)
        request = self.rf.get("/dashboard/")
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

    def test_complete_user_passes_through(self, db):
        user = UserFactory(email="complete@test.com", setup_status="complete")
        request = self.rf.get("/dashboard/")
        request.user = user
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    @patch("core.inertia.middleware.SetupStatusService")
    def test_incomplete_user_redirected(self, mock_service_cls, db):
        user = UserFactory(email="incomplete@test.com", incomplete_setup=True)
        mock_status = MagicMock()
        mock_status.is_complete = False
        mock_status.redirect_url = "/onboarding/verify-email/"
        mock_service_cls.get_setup_status.return_value = mock_status

        request = self.rf.get("/dashboard/")
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
        request = self.rf.get("/dashboard/")
        request.user = AnonymousUser()
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_non_delinquent_user_passes(self, db):
        user = UserFactory(email="good@test.com")
        request = self.rf.get("/dashboard/")
        request.user = user
        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_delinquent_user_redirected(self, db):
        user = UserFactory(email="deli@test.com")
        # Mock is_delinquent property
        user.is_delinquent = True

        request = self.rf.get("/dashboard/")
        request.user = user

        response = self.middleware(request)
        assert response.status_code == 302
        assert response.url == "/delinquent/"

    def test_delinquent_user_can_access_billing(self, db):
        user = UserFactory(email="deli2@test.com")
        user.is_delinquent = True

        request = self.rf.get("/billing/")
        request.user = user

        self.middleware(request)
        self.get_response.assert_called_once_with(request)

    def test_delinquent_user_can_access_logout(self, db):
        user = UserFactory(email="deli3@test.com")
        user.is_delinquent = True

        request = self.rf.get("/auth/logout/")
        request.user = user

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
