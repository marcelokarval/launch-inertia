"""
Unit tests for identity services: AuthService, RegistrationService, TokenService.
"""
# pyright: reportOptionalMemberAccess=false, reportAssignmentType=false, reportAttributeAccessIssue=false

import pytest
from unittest.mock import patch
from django.test import RequestFactory

from apps.identity.models import User
from apps.identity.services.auth_service import AuthService
from apps.identity.services.registration_service import RegistrationService
from apps.identity.services.token_service import TokenService
from tests.factories import UserFactory, ProfileFactory


# ── AuthService Tests ────────────────────────────────────────────────


class TestAuthServiceLogin:
    """Tests for AuthService.login()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.rf = RequestFactory()
        self.user = UserFactory(
            email="login@test.com",
            email_verified=True,
            status="active",
        )

    def _make_request(self):
        request = self.rf.post("/auth/login/")
        request.session = {}
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        # Simulate session middleware
        from django.contrib.sessions.backends.db import SessionStore

        request.session = SessionStore()
        return request

    def test_login_success(self):
        request = self._make_request()
        result = AuthService.login("login@test.com", "testpass123", request)
        assert result.success is True
        assert result.message == "Welcome back!"

    def test_login_wrong_password(self):
        request = self._make_request()
        result = AuthService.login("login@test.com", "wrongpass", request)
        assert result.success is False
        assert "Invalid email or password" in result.message

    def test_login_nonexistent_email(self):
        request = self._make_request()
        result = AuthService.login("nobody@test.com", "pass", request)
        assert result.success is False
        assert "Invalid email or password" in result.message

    def test_login_empty_fields(self):
        request = self._make_request()
        result = AuthService.login("", "", request)
        assert result.success is False

    def test_login_unverified_email(self):
        UserFactory(
            email="unver@test.com",
            email_verified=False,
            status="pending",
        )
        request = self._make_request()
        result = AuthService.login("unver@test.com", "testpass123", request)
        assert result.success is False
        assert "verify" in result.message.lower()

    def test_login_locked_account(self):
        self.user.status = User.Status.LOCKED
        self.user.set_metadata("locked_at", "2099-01-01T00:00:00+00:00")
        self.user.save()

        request = self._make_request()
        result = AuthService.login("login@test.com", "testpass123", request)
        assert result.success is False
        assert "locked" in result.message.lower()

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        request = self._make_request()
        result = AuthService.login("login@test.com", "testpass123", request)
        assert result.success is False
        assert "inactive" in result.message.lower()

    def test_failed_login_increments_counter(self):
        request = self._make_request()
        assert self.user.failed_login_attempts == 0

        AuthService.login("login@test.com", "wrong", request)
        self.user.refresh_from_db()
        assert self.user.failed_login_attempts == 1


class TestAuthServiceChangePassword:
    """Tests for AuthService.change_password()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="changepw@test.com")

    def test_change_password_success(self):
        result = AuthService.change_password(self.user, "testpass123", "newpass12345")
        assert result.success is True
        self.user.refresh_from_db()
        assert self.user.check_password("newpass12345")

    def test_change_password_wrong_old(self):
        result = AuthService.change_password(self.user, "wrongold", "newpass12345")
        assert result.success is False
        assert "old_password" in result.errors

    def test_change_password_too_short(self):
        result = AuthService.change_password(self.user, "testpass123", "short")
        assert result.success is False
        assert "new_password" in result.errors

    def test_change_password_empty_fields(self):
        result = AuthService.change_password(self.user, "", "")
        assert result.success is False


class TestAuthServicePasswordReset:
    """Tests for AuthService.reset_password_request() and reset_password_confirm()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="reset@test.com")

    @patch("apps.identity.tasks.send_password_reset_email_task")
    def test_reset_request_existing_email(self, mock_task):
        result = AuthService.reset_password_request("reset@test.com")
        assert result["success"] is True
        mock_task.delay.assert_called_once()

    def test_reset_request_nonexistent_email(self):
        """Anti-enumeration: same message for non-existent email."""
        result = AuthService.reset_password_request("nobody@test.com")
        assert result["success"] is True

    @patch("apps.identity.tasks.send_password_reset_email_task")
    def test_reset_confirm_success(self, mock_task):
        token = TokenService.create_password_reset_token(self.user)
        result = AuthService.reset_password_confirm(token, "newpass12345")
        assert result.success is True
        self.user.refresh_from_db()
        assert self.user.check_password("newpass12345")

    def test_reset_confirm_invalid_code(self):
        result = AuthService.reset_password_confirm("999999", "newpass12345")
        assert result.success is False


# ── RegistrationService Tests ────────────────────────────────────────


class TestRegistrationService:
    """Tests for RegistrationService.register() and verify_email()."""

    @patch("apps.identity.tasks.send_verification_email_task")
    def test_register_success(self, mock_task, db):
        result = RegistrationService.register(
            email="new@test.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        assert result.success is True
        assert User.objects.filter(email="new@test.com").exists()
        mock_task.delay.assert_called_once()

    def test_register_missing_fields(self, db):
        result = RegistrationService.register(
            email="",
            password="",
            first_name="",
            last_name="",
        )
        assert result.success is False
        assert "email" in result.errors

    @patch("apps.identity.tasks.send_verification_email_task")
    def test_register_duplicate_email_anti_enumeration(self, mock_task, db):
        """Duplicate email returns success (anti-enumeration)."""
        UserFactory(email="existing@test.com")
        result = RegistrationService.register(
            email="existing@test.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        # Anti-enumeration: same response as success
        assert result.success is True

    @patch("apps.identity.tasks.send_verification_email_task")
    def test_register_creates_profile(self, mock_task, db):
        RegistrationService.register(
            email="withprofile@test.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        from apps.identity.models import Profile

        user = User.objects.get(email="withprofile@test.com")
        assert Profile.objects.filter(user=user).exists()

    @patch("apps.identity.tasks.send_verification_email_task")
    def test_verify_email_success(self, mock_task, db):
        user = UserFactory(email="verify@test.com", unverified=True)
        token = TokenService.create_email_verification_token(user, user.email)

        success, message, verified_user = RegistrationService.verify_email(token)
        assert success is True
        verified_user.refresh_from_db()
        assert verified_user.email_verified is True

    def test_verify_email_invalid_code(self, db):
        success, message, user = RegistrationService.verify_email("000000")
        assert success is False
        assert user is None


# ── TokenService Tests ───────────────────────────────────────────────


class TestTokenService:
    """Tests for TokenService."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="tokens@test.com")

    def test_create_email_verification_token(self):
        token = TokenService.create_email_verification_token(self.user, self.user.email)
        assert len(token) == 6
        assert token.isdigit()

    def test_verify_email_verification_token(self):
        token = TokenService.create_email_verification_token(self.user, self.user.email)
        success, message, user = TokenService.verify_email_verification_token(token)
        assert success is True
        assert user == self.user

    def test_verify_invalid_token(self):
        success, message, user = TokenService.verify_email_verification_token("000000")
        assert success is False
        assert user is None

    def test_verify_used_token(self):
        token = TokenService.create_email_verification_token(self.user, self.user.email)
        # First verification
        TokenService.verify_email_verification_token(token)
        # Second attempt should fail
        success, message, user = TokenService.verify_email_verification_token(token)
        assert success is False

    def test_create_password_reset_token(self):
        token = TokenService.create_password_reset_token(self.user)
        assert len(token) == 6
        assert token.isdigit()

    def test_rate_limit_email_verification(self):
        """Rate limit: max 3 tokens per hour."""
        for _ in range(3):
            TokenService.create_email_verification_token(self.user, self.user.email)

        with pytest.raises(ValueError, match="Too many"):
            TokenService.create_email_verification_token(self.user, self.user.email)

    def test_cleanup_expired_tokens(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.identity.models.token_models import UserToken

        # Create an already-expired token
        token = TokenService.create_email_verification_token(self.user, self.user.email)
        UserToken.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )

        count = TokenService.cleanup_expired_tokens()
        assert count >= 1

    def test_invalidate_user_tokens(self):
        from apps.identity.models.token_models import UserToken

        TokenService.create_password_reset_token(self.user)
        count = TokenService.invalidate_user_tokens(
            self.user, UserToken.TokenType.PASSWORD_RESET
        )
        assert count == 1
