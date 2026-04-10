"""
Registration service for user signup and email verification.

Handles the complete registration flow including user creation,
profile creation, email verification, and anti-enumeration protections.
"""

import logging
from dataclasses import dataclass, field

from django.db import transaction

from apps.identity.models import User, Profile
from .token_service import TokenService

logger = logging.getLogger(__name__)


@dataclass
class RegistrationResult:
    """Result of a registration attempt."""

    success: bool
    message: str
    errors: dict = field(default_factory=dict)
    user: User | None = None


class RegistrationService:
    """
    Service for user registration operations.

    All methods are static/class methods. No instance state.
    Handles registration, email verification, and resending verification emails.
    """

    @staticmethod
    @transaction.atomic
    def register(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> RegistrationResult:
        """
        Register a new user.

        Creates the user and profile atomically, then sends a verification
        email asynchronously. Uses anti-enumeration: does not reveal whether
        the email already exists.

        Args:
            email: User's email address.
            password: User's chosen password.
            first_name: User's first name.
            last_name: User's last name.

        Returns:
            RegistrationResult with success status and details.
        """
        email = email.lower().strip() if email else ""

        # Validate input
        errors = {}
        if not email:
            errors["email"] = ["Email is required."]
        if not password:
            errors["password"] = ["Password is required."]
        if not first_name:
            errors["first_name"] = ["First name is required."]
        if not last_name:
            errors["last_name"] = ["Last name is required."]

        if len(password) < 8 if password else False:
            errors["password"] = ["Password must be at least 8 characters long."]

        if errors:
            return RegistrationResult(
                success=False,
                message="Please correct the errors below.",
                errors=errors,
            )

        # Check if email already exists (anti-enumeration: same success message)
        if User.objects.filter(email=email).exists():
            logger.info("Registration attempted with existing email: %s", email)
            # Return same message as success to prevent enumeration
            return RegistrationResult(
                success=True,
                message=(
                    "Account created! Please check your email to verify your account."
                ),
            )

        # Create user
        user = User.objects.create_user(  # type: ignore[call-arg]
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Create profile
        Profile.objects.create(user=user)

        # Send verification email (async via Celery)
        try:
            display_token = TokenService.create_email_verification_token(user, email)
            from apps.identity.tasks import send_verification_email_task

            send_verification_email_task.delay(
                user_id=user.pk,
                display_token=display_token,
            )
            logger.info(
                "Verification email task queued for new user %s",
                user.public_id,
            )
        except ValueError:
            logger.exception("Rate limit hit during registration for: %s", email)
        except Exception:
            logger.exception("Error creating verification token for: %s", email)

        # Fire user_registered signal
        from apps.identity.signals import user_registered

        user_registered.send(sender=RegistrationService, user=user)

        logger.info("New user registered: %s (%s)", email, user.public_id)

        return RegistrationResult(
            success=True,
            message=(
                "Account created! Please check your email to verify your account."
            ),
            user=user,
        )

    @staticmethod
    @transaction.atomic
    def verify_email(
        verification_code: str,
    ) -> tuple[bool, str, User | None]:
        """
        Verify a user's email using a verification code.

        Args:
            verification_code: The 6-digit OTP from the verification email.

        Returns:
            Tuple of (success, message, user_or_none).
        """
        success, message, user = TokenService.verify_email_verification_token(
            verification_code
        )

        if success and user:
            # Mark the user's email as verified
            user.verify_email()
            logger.info("Email verified for user: %s", user.email)

            # Fire email_verified signal (triggers welcome email, notification)
            from apps.identity.signals import email_verified

            email_verified.send(sender=RegistrationService, user=user)

        return success, message, user

    @staticmethod
    def resend_verification_email(email: str) -> tuple[bool, str]:
        """
        Resend a verification email.

        Anti-enumeration: always returns a success message regardless
        of whether the email exists or is already verified.

        Args:
            email: The email address to resend verification to.

        Returns:
            Tuple of (success, message).
        """
        email = email.lower().strip() if email else ""

        # Anti-enumeration: always return same message
        success_message = (
            "If an account exists with that email and is not yet verified, "
            "you will receive a new verification code."
        )

        if not email:
            return True, success_message

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.info(
                "Verification resend requested for non-existent email: %s",
                email,
            )
            return True, success_message

        # Don't resend if already verified
        if user.email_verified:
            logger.info(
                "Verification resend requested for already-verified email: %s",
                email,
            )
            return True, success_message

        # Create new verification token and send async
        try:
            display_token = TokenService.create_email_verification_token(user, email)
            from apps.identity.tasks import send_verification_email_task

            send_verification_email_task.delay(
                user_id=user.pk,
                display_token=display_token,
            )
            logger.info(
                "Verification email task queued for user %s (resend)",
                user.public_id,
            )
        except ValueError as e:
            logger.info("Rate limit on resend for %s: %s", email, str(e))
            return False, str(e)
        except Exception:
            logger.exception("Error resending verification for: %s", email)

        return True, success_message
