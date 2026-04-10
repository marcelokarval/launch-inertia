"""
Token service for creating and verifying authentication tokens.

Handles email verification tokens, password reset tokens, and rate limiting.
All tokens use 6-digit OTPs with SHA-256 hashed storage.
"""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.identity.models import User
from apps.identity.models.token_models import UserToken, EmailVerificationToken

logger = logging.getLogger(__name__)


class TokenService:
    """
    Service for managing authentication tokens.

    All methods are static/class methods. No instance state.
    """

    # Configuration constants
    EMAIL_VERIFICATION_EXPIRY_HOURS = 24
    PASSWORD_RESET_EXPIRY_HOURS = 1
    EMAIL_VERIFICATION_RATE_LIMIT = 3  # max per hour per user

    @staticmethod
    @transaction.atomic
    def create_email_verification_token(user: User, email: str) -> str:
        """
        Create a new email verification token.

        Rate limited to 3 tokens per hour per user to prevent abuse.

        Args:
            user: The user requesting verification.
            email: The email address to verify.

        Returns:
            The 6-digit display token string.

        Raises:
            ValueError: If rate limit is exceeded.
        """
        # Rate limit: max 3 per hour per user
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_count = UserToken.objects.filter(
            user=user,
            token_type=UserToken.TokenType.EMAIL_VERIFICATION,
            created_at__gte=one_hour_ago,
        ).count()

        if recent_count >= TokenService.EMAIL_VERIFICATION_RATE_LIMIT:
            raise ValueError(
                "Too many verification requests. Please wait before trying again."
            )

        # Generate OTP and hash
        display_token = UserToken.generate_otp()
        token_hash = UserToken.hash_token(display_token)

        # Create UserToken
        user_token = UserToken.objects.create(
            user=user,
            token_hash=token_hash,
            display_token=display_token,
            token_type=UserToken.TokenType.EMAIL_VERIFICATION,
            expires_at=timezone.now()
            + timedelta(hours=TokenService.EMAIL_VERIFICATION_EXPIRY_HOURS),
        )

        # Create EmailVerificationToken
        EmailVerificationToken.objects.create(
            token=user_token,
            email=email,
        )

        logger.info(
            "Email verification token created for user %s (email: %s)",
            user.public_id,
            email,
        )

        return display_token

    @staticmethod
    @transaction.atomic
    def verify_email_verification_token(
        display_token: str,
    ) -> tuple[bool, str, User | None]:
        """
        Verify an email verification token using timing-safe comparison.

        Args:
            display_token: The 6-digit OTP entered by the user.

        Returns:
            Tuple of (success, message, user_or_none).
        """
        token_hash = UserToken.hash_token(display_token)

        # Find matching, unused, unexpired token
        try:
            user_token = UserToken.objects.select_related("user").get(
                token_hash=token_hash,
                token_type=UserToken.TokenType.EMAIL_VERIFICATION,
                is_used=False,
            )
        except UserToken.DoesNotExist:
            logger.warning("Invalid email verification token attempted")
            return False, "Invalid or expired verification code.", None
        except UserToken.MultipleObjectsReturned:
            # Edge case: hash collision or duplicate. Take the most recent.
            user_token = (
                UserToken.objects.select_related("user")
                .filter(
                    token_hash=token_hash,
                    token_type=UserToken.TokenType.EMAIL_VERIFICATION,
                    is_used=False,
                )
                .order_by("-created_at")
                .first()
            )

        if user_token is None:
            return False, "Invalid or expired verification code.", None

        # Timing-safe verification
        if not user_token.verify(display_token):
            return False, "Invalid or expired verification code.", None

        # Mark token as used
        user_token.mark_used()

        # Get the associated email verification
        email_verification = user_token.email_verifications.first()
        if email_verification:
            logger.info(
                "Email verification successful for user %s (email: %s)",
                user_token.user.public_id,
                email_verification.email,
            )

        return True, "Email verified successfully.", user_token.user

    @staticmethod
    @transaction.atomic
    def create_password_reset_token(user: User) -> str:
        """
        Create a password reset token.

        Invalidates any previous unused password reset tokens for the user.
        Password reset tokens expire after 1 hour.

        Args:
            user: The user requesting a password reset.

        Returns:
            The 6-digit display token string.
        """
        # Invalidate previous reset tokens
        TokenService.invalidate_user_tokens(user, UserToken.TokenType.PASSWORD_RESET)

        # Generate OTP and hash
        display_token = UserToken.generate_otp()
        token_hash = UserToken.hash_token(display_token)

        UserToken.objects.create(
            user=user,
            token_hash=token_hash,
            display_token=display_token,
            token_type=UserToken.TokenType.PASSWORD_RESET,
            expires_at=timezone.now()
            + timedelta(hours=TokenService.PASSWORD_RESET_EXPIRY_HOURS),
        )

        logger.info(
            "Password reset token created for user %s",
            user.public_id,
        )

        return display_token

    @staticmethod
    def invalidate_user_tokens(user: User, token_type: str) -> int:
        """
        Invalidate all unused tokens of a given type for a user.

        Args:
            user: The user whose tokens to invalidate.
            token_type: The type of tokens to invalidate.

        Returns:
            Number of tokens invalidated.
        """
        updated = UserToken.objects.filter(
            user=user,
            token_type=token_type,
            is_used=False,
        ).update(
            is_used=True,
            used_at=timezone.now(),
        )

        if updated:
            logger.info(
                "Invalidated %d %s tokens for user %s",
                updated,
                token_type,
                user.public_id,
            )

        return updated

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """
        Delete all expired and used tokens from the database.

        Should be run periodically via a management command or Celery task.

        Returns:
            Number of tokens deleted.
        """
        now = timezone.now()

        # Delete expired tokens
        expired_tokens = UserToken.objects.filter(
            expires_at__lt=now,
        )
        count = expired_tokens.count()
        expired_tokens.delete()

        # Delete used tokens older than 7 days (keep for audit trail)
        seven_days_ago = now - timedelta(days=7)
        old_used_tokens = UserToken.objects.filter(
            is_used=True,
            used_at__lt=seven_days_ago,
        )
        old_count = old_used_tokens.count()
        old_used_tokens.delete()

        total = count + old_count
        if total:
            logger.info(
                "Cleaned up %d tokens (%d expired, %d old used)",
                total,
                count,
                old_count,
            )

        return total
