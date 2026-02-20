"""
Authentication service for login, logout, and password management.

Encapsulates all authentication business logic, including account lockout,
session management, and password reset flows.

Integrates with SecurityEventDetector for security monitoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import cast

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from apps.identity.models import User
from apps.identity.models.token_models import UserToken
from .token_service import TokenService

logger = logging.getLogger(__name__)


def _get_security_detector():
    """Lazy import to avoid circular imports. Returns None on failure."""
    try:
        from core.security.monitoring import security_detector

        return security_detector
    except Exception:
        return None


@dataclass
class LoginResult:
    """Result of a login attempt."""

    success: bool
    message: str
    errors: dict = field(default_factory=dict)
    user: User | None = None
    redirect_url: str | None = None


@dataclass
class PasswordChangeResult:
    """Result of a password change operation."""

    success: bool
    message: str
    errors: dict = field(default_factory=dict)


class AuthService:
    """
    Service for authentication operations.

    All methods are static/class methods. No instance state.
    Handles login, logout, password changes, and password resets.
    """

    # Configuration constants
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    REMEMBER_ME_DURATION_DAYS = 30

    @staticmethod
    def login(
        email: str,
        password: str,
        request: HttpRequest,
        remember_me: bool = False,
    ) -> LoginResult:
        """
        Authenticate a user and create a session.

        Full flow:
        1. Validate input
        2. Check if user exists
        3. Check account lockout
        4. Check if user is active
        5. Authenticate credentials
        6. Check if email is verified
        7. Create session with appropriate expiry

        Args:
            email: User's email address.
            password: User's password.
            request: The HTTP request object.
            remember_me: Whether to extend session duration.

        Returns:
            LoginResult with success status and details.
        """
        email = email.lower().strip() if email else ""

        # Validate input
        if not email or not password:
            return LoginResult(
                success=False,
                message="Please provide both email and password.",
                errors={"__all__": ["Please provide both email and password."]},
            )

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Anti-enumeration: don't reveal if email exists
            logger.info("Login attempt for non-existent email: %s", email)
            return LoginResult(
                success=False,
                message="Invalid email or password.",
                errors={"__all__": ["Invalid email or password."]},
            )

        # Check account lockout
        if AuthService._is_account_locked(user):
            logger.warning("Login attempt on locked account: %s", email)
            return LoginResult(
                success=False,
                message="This account has been temporarily locked due to too many "
                "failed attempts. Please try again later.",
                errors={
                    "__all__": [
                        "This account has been temporarily locked. "
                        "Please try again later."
                    ]
                },
            )

        # Check if user is active
        if not user.is_active:
            logger.warning("Login attempt on inactive account: %s", email)
            return LoginResult(
                success=False,
                message="This account is inactive.",
                errors={"__all__": ["This account is inactive."]},
            )

        # Authenticate
        _authenticated_user = authenticate(request, username=email, password=password)

        if _authenticated_user is None:
            # Record failed attempt
            AuthService._record_failed_login(user)
            logger.info("Failed login attempt for: %s", email)

            # Record security event
            detector = _get_security_detector()
            if detector:
                detector.record_failed_login(
                    ip_address=request.META.get("REMOTE_ADDR", "unknown"),
                    email=email,
                )

            return LoginResult(
                success=False,
                message="Invalid email or password.",
                errors={"__all__": ["Invalid email or password."]},
            )

        # authenticate() succeeded — we know it's our concrete User model
        authenticated_user = cast(User, _authenticated_user)

        # Check email verification
        if not authenticated_user.email_verified:
            logger.info("Login attempt with unverified email: %s", email)
            return LoginResult(
                success=False,
                message="Please verify your email address before logging in.",
                errors={
                    "__all__": ["Please verify your email address before logging in."]
                },
            )

        # Successful authentication - create session
        login(request, authenticated_user)

        # Set session expiry
        if remember_me:
            request.session.set_expiry(
                timedelta(days=AuthService.REMEMBER_ME_DURATION_DAYS)
            )
        else:
            # Browser session (expires when browser closes)
            request.session.set_expiry(0)

        # Clear failed login attempts and record login
        AuthService._clear_failed_logins(authenticated_user)
        ip_address = request.META.get("REMOTE_ADDR", "")
        authenticated_user.record_login(ip_address)

        logger.info("Successful login for: %s", email)

        # Record security event
        detector = _get_security_detector()
        if detector:
            detector.record_successful_login(
                user_id=str(authenticated_user.id),
                ip_address=request.META.get("REMOTE_ADDR", "unknown"),
            )

        return LoginResult(
            success=True,
            message="Welcome back!",
            user=authenticated_user,
            redirect_url="identity:dashboard",
        )

    @staticmethod
    def logout(request: HttpRequest) -> bool:
        """
        Log out the current user.

        Args:
            request: The HTTP request object.

        Returns:
            True if logout was successful.
        """
        if request.user.is_authenticated:
            user = cast(User, request.user)
            logger.info("User logged out: %s", user.email)
        logout(request)
        return True

    @staticmethod
    @transaction.atomic
    def change_password(
        user: User,
        old_password: str,
        new_password: str,
    ) -> PasswordChangeResult:
        """
        Change a user's password.

        Args:
            user: The authenticated user.
            old_password: The current password.
            new_password: The new password.

        Returns:
            PasswordChangeResult with success status and details.
        """
        # Validate input
        if not old_password or not new_password:
            return PasswordChangeResult(
                success=False,
                message="Please provide both current and new passwords.",
                errors={"__all__": ["Please provide both current and new passwords."]},
            )

        # Verify old password
        if not user.check_password(old_password):
            return PasswordChangeResult(
                success=False,
                message="Current password is incorrect.",
                errors={"old_password": ["Current password is incorrect."]},
            )

        # Validate new password length
        if len(new_password) < 8:
            return PasswordChangeResult(
                success=False,
                message="New password must be at least 8 characters long.",
                errors={
                    "new_password": ["New password must be at least 8 characters long."]
                },
            )

        # Set new password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        logger.info("Password changed for user: %s", user.email)

        return PasswordChangeResult(
            success=True,
            message="Password changed successfully.",
        )

    @staticmethod
    def reset_password_request(email: str) -> dict:
        """
        Request a password reset.

        Always returns a success message to prevent email enumeration.
        If the email exists, creates a reset token and would send an email.

        Args:
            email: The email address to send the reset to.

        Returns:
            Dict with 'success' and 'message' keys.
        """
        email = email.lower().strip() if email else ""

        # Anti-enumeration: always return success
        result = {
            "success": True,
            "message": (
                "If an account exists with that email, "
                "you will receive a password reset code."
            ),
        }

        if not email:
            return result

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            logger.info("Password reset requested for non-existent email: %s", email)
            return result

        # Create reset token and send email async
        try:
            display_token = TokenService.create_password_reset_token(user)
            from apps.identity.tasks import send_password_reset_email_task

            send_password_reset_email_task.delay(
                user_id=user.pk,
                display_token=display_token,
            )
            logger.info("Password reset email task queued for: %s", email)
        except Exception:
            logger.exception("Error creating password reset token for: %s", email)

        return result

    @staticmethod
    @transaction.atomic
    def reset_password_confirm(
        verification_code: str,
        new_password: str,
    ) -> PasswordChangeResult:
        """
        Confirm a password reset using a verification code.

        Args:
            verification_code: The 6-digit OTP from the reset email.
            new_password: The new password.

        Returns:
            PasswordChangeResult with success status and details.
        """
        if not verification_code or not new_password:
            return PasswordChangeResult(
                success=False,
                message="Please provide both verification code and new password.",
                errors={
                    "__all__": [
                        "Please provide both verification code and new password."
                    ]
                },
            )

        # Validate new password length
        if len(new_password) < 8:
            return PasswordChangeResult(
                success=False,
                message="New password must be at least 8 characters long.",
                errors={
                    "new_password": ["New password must be at least 8 characters long."]
                },
            )

        # Find the token
        token_hash = UserToken.hash_token(verification_code)
        try:
            user_token = UserToken.objects.select_related("user").get(
                token_hash=token_hash,
                token_type=UserToken.TokenType.PASSWORD_RESET,
                is_used=False,
            )
        except UserToken.DoesNotExist:
            return PasswordChangeResult(
                success=False,
                message="Invalid or expired reset code.",
                errors={"__all__": ["Invalid or expired reset code."]},
            )

        # Verify token (timing-safe)
        if not user_token.verify(verification_code):
            return PasswordChangeResult(
                success=False,
                message="Invalid or expired reset code.",
                errors={"__all__": ["Invalid or expired reset code."]},
            )

        # Set new password
        user = user_token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Mark token as used
        user_token.mark_used()

        # Invalidate all other reset tokens
        TokenService.invalidate_user_tokens(user, UserToken.TokenType.PASSWORD_RESET)

        # Unlock account if locked
        if user.status == User.Status.LOCKED:
            user.unlock_account()

        logger.info("Password reset confirmed for user: %s", user.email)

        return PasswordChangeResult(
            success=True,
            message="Password has been reset successfully. You can now log in.",
        )

    @staticmethod
    def _is_account_locked(user: User) -> bool:
        """
        Check if a user's account is currently locked.

        Accounts are locked after MAX_FAILED_ATTEMPTS failed login attempts.
        The lockout expires after LOCKOUT_DURATION_MINUTES.

        Args:
            user: The user to check.

        Returns:
            True if the account is currently locked.
        """
        if user.status != User.Status.LOCKED:
            return False

        # Check if lockout period has expired
        locked_at_str = user.get_metadata("locked_at")
        if locked_at_str:
            from django.utils.dateparse import parse_datetime

            locked_at = parse_datetime(locked_at_str)
            if locked_at:
                lockout_expires = locked_at + timedelta(
                    minutes=AuthService.LOCKOUT_DURATION_MINUTES
                )
                if timezone.now() >= lockout_expires:
                    # Lockout expired, unlock the account
                    user.unlock_account()
                    return False

        return True

    @staticmethod
    def _record_failed_login(user: User) -> None:
        """
        Record a failed login attempt for a user.

        After MAX_FAILED_ATTEMPTS, the account is locked.
        Records a security event if the account becomes locked.

        Args:
            user: The user who failed to log in.
        """
        was_locked = user.status == User.Status.LOCKED
        user.record_failed_login()

        # If the account just got locked, record a high-severity security event
        if not was_locked and user.status == User.Status.LOCKED:
            detector = _get_security_detector()
            if detector:
                detector.record_account_locked(
                    user_id=str(user.id),
                    reason=f"Too many failed login attempts ({AuthService.MAX_FAILED_ATTEMPTS})",
                )

    @staticmethod
    def _clear_failed_logins(user: User) -> None:
        """
        Clear failed login counter for a user.

        Called after a successful login.

        Args:
            user: The user who logged in successfully.
        """
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.save(update_fields=["failed_login_attempts"])
