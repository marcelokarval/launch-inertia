"""
Token models for authentication flows.

Provides secure OTP-based tokens for email verification, password reset,
and other authentication operations. Uses SHA-256 hashing for token storage
and HMAC compare_digest for timing-safe verification.
"""

from __future__ import annotations

import hashlib
import hmac
import random
import string
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.shared.models import BaseModel

if TYPE_CHECKING:
    from django.db.models import Manager


class UserToken(BaseModel):
    """
    Secure token for authentication operations.

    Stores a SHA-256 hash of the token rather than the raw value.
    The display_token (6-digit OTP) is what the user sees and enters.
    Verification uses hmac.compare_digest for timing-safe comparison.
    """

    PUBLIC_ID_PREFIX = "tkn"

    # -- Pyright: reverse relation managers --
    if TYPE_CHECKING:
        email_verifications: Manager[EmailVerificationToken]

    class TokenType(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", "Email Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"
        API = "api", "API Token"
        SESSION = "session", "Session Token"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tokens",
    )
    token_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of the token value",
    )
    display_token = models.CharField(
        max_length=6,
        help_text="6-digit OTP shown to the user",
    )
    token_type = models.CharField(
        max_length=30,
        choices=TokenType.choices,
        db_index=True,
    )
    expires_at = models.DateTimeField(
        help_text="When this token expires",
    )
    is_used = models.BooleanField(
        default=False,
        db_index=True,
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when token was created",
    )
    used_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when token was used",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string when token was created",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "User Token"
        verbose_name_plural = "User Tokens"
        indexes = [
            models.Index(
                fields=["user", "token_type", "is_used"],
                name="idx_token_user_type_used",
            ),
            models.Index(
                fields=["expires_at", "is_used"],
                name="idx_token_expiry_used",
            ),
        ]

    def __str__(self):
        return f"{self.token_type} token for {self.user} ({self.public_id})"

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random numeric OTP of the specified length."""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def hash_token(token: str) -> str:
        """Create a SHA-256 hash of the given token string."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def verify(self, display_token: str) -> bool:
        """
        Timing-safe verification of the display token.

        Compares the SHA-256 hash of the provided token against the stored hash
        using hmac.compare_digest to prevent timing attacks.

        Args:
            display_token: The 6-digit OTP entered by the user.

        Returns:
            True if token matches and is still valid, False otherwise.
        """
        if self.is_used or self.is_expired:
            return False

        candidate_hash = self.hash_token(display_token)
        return hmac.compare_digest(candidate_hash, self.token_hash)

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return timezone.now() >= self.expires_at

    def mark_used(self, ip: str | None = None) -> None:
        """
        Mark the token as used.

        Args:
            ip: IP address of the request that consumed the token.
        """
        self.is_used = True
        self.used_at = timezone.now()
        if ip:
            self.used_ip = ip
        self.save(update_fields=["is_used", "used_at", "used_ip"])

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """
        Delete all expired and used tokens.

        Returns:
            Number of tokens deleted.
        """
        expired = cls.objects.filter(
            models.Q(expires_at__lt=timezone.now()) | models.Q(is_used=True),
        )
        count, _ = expired.delete()
        return count


class EmailVerificationToken(BaseModel):
    """
    Links a UserToken to a specific email address for email verification.

    This allows verifying email changes as well as initial registration
    email verification.
    """

    PUBLIC_ID_PREFIX = "evt"

    token = models.ForeignKey(
        UserToken,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )
    email = models.EmailField(
        db_index=True,
        help_text="The email address being verified",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        indexes = [
            models.Index(
                fields=["email", "created_at"],
                name="idx_evt_email_created",
            ),
        ]

    def __str__(self):
        return f"Email verification for {self.email} ({self.public_id})"
