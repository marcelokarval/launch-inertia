"""
Email/phone verification service.

Generates verification codes/tokens and validates them.
Ported from legacy contact/services/verification_service.py.

Verification data is stored in the model's metadata JSONField:
- verification_code: numeric code (e.g., "123456")
- verification_token: alphanumeric token (e.g., "a1b2c3...")
- verification_expiry: ISO timestamp when code/token expires
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Handles verification code/token generation and validation
    for ContactEmail and ContactPhone records.
    """

    # ── Code Generation ──────────────────────────────────────────────

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a random numeric verification code."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def generate_verification_token(length: int = 32) -> str:
        """Generate a random alphanumeric verification token."""
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    # ── Email Verification ───────────────────────────────────────────

    @classmethod
    def send_email_verification(
        cls,
        email_obj,
        code: Optional[str] = None,
        token: Optional[str] = None,
        expiry_hours: int = 24,
    ) -> dict:
        """
        Prepare email verification (stores code/token in metadata).

        In production, this would trigger an email send via EmailService.
        Here we just store the verification data.

        Args:
            email_obj: ContactEmail instance.
            code: Optional pre-generated code. Auto-generated if not provided.
            token: Optional pre-generated token. Auto-generated if not provided.
            expiry_hours: Hours until code/token expires (default: 24).

        Returns:
            Dict with code, token, and expiry timestamp.
        """
        if not code:
            code = cls.generate_verification_code()
        if not token:
            token = cls.generate_verification_token()

        expiry = timezone.now() + timedelta(hours=expiry_hours)

        email_obj.update_metadata(
            {
                "verification_code": code,
                "verification_token": token,
                "verification_expiry": expiry.isoformat(),
            }
        )

        logger.info("Verification prepared for email: %s", email_obj.value)

        return {
            "code": code,
            "token": token,
            "expiry": expiry.isoformat(),
        }

    @classmethod
    def verify_email_with_code(cls, email_obj, code: str) -> bool:
        """
        Verify an email using a numeric code.

        Args:
            email_obj: ContactEmail instance.
            code: The code to validate.

        Returns:
            True if verification succeeded, False otherwise.
        """
        stored_code = email_obj.get_metadata("verification_code")
        expiry_str = email_obj.get_metadata("verification_expiry")

        if not stored_code or not expiry_str:
            logger.warning("No verification data for email: %s", email_obj.value)
            return False

        expiry = datetime.fromisoformat(expiry_str)
        if timezone.now() > expiry:
            logger.warning("Verification code expired for email: %s", email_obj.value)
            return False

        if stored_code != code:
            logger.warning("Invalid verification code for email: %s", email_obj.value)
            return False

        # Mark as verified and clean up
        email_obj.verify()
        email_obj.remove_metadata("verification_code")
        email_obj.remove_metadata("verification_token")
        email_obj.remove_metadata("verification_expiry")

        logger.info("Email verified via code: %s", email_obj.value)
        return True

    @classmethod
    def verify_email_with_token(cls, email_obj, token: str) -> bool:
        """
        Verify an email using an alphanumeric token (for email links).

        Args:
            email_obj: ContactEmail instance.
            token: The token to validate.

        Returns:
            True if verification succeeded, False otherwise.
        """
        stored_token = email_obj.get_metadata("verification_token")
        expiry_str = email_obj.get_metadata("verification_expiry")

        if not stored_token or not expiry_str:
            return False

        expiry = datetime.fromisoformat(expiry_str)
        if timezone.now() > expiry:
            return False

        if stored_token != token:
            return False

        email_obj.verify()
        email_obj.remove_metadata("verification_code")
        email_obj.remove_metadata("verification_token")
        email_obj.remove_metadata("verification_expiry")

        logger.info("Email verified via token: %s", email_obj.value)
        return True

    # ── Phone Verification ───────────────────────────────────────────

    @classmethod
    def send_phone_verification(
        cls,
        phone_obj,
        code: Optional[str] = None,
        expiry_minutes: int = 15,
    ) -> dict:
        """
        Prepare phone verification (stores code in metadata).

        In production, this would trigger an SMS send.

        Args:
            phone_obj: ContactPhone instance.
            code: Optional pre-generated code. Auto-generated if not provided.
            expiry_minutes: Minutes until code expires (default: 15).

        Returns:
            Dict with code and expiry timestamp.
        """
        if not code:
            code = cls.generate_verification_code()

        expiry = timezone.now() + timedelta(minutes=expiry_minutes)

        phone_obj.update_metadata(
            {
                "verification_code": code,
                "verification_expiry": expiry.isoformat(),
            }
        )

        logger.info("Verification prepared for phone: %s", phone_obj.value)

        return {
            "code": code,
            "expiry": expiry.isoformat(),
        }

    @classmethod
    def verify_phone_with_code(cls, phone_obj, code: str) -> bool:
        """
        Verify a phone number using a numeric code.

        Args:
            phone_obj: ContactPhone instance.
            code: The code to validate.

        Returns:
            True if verification succeeded, False otherwise.
        """
        stored_code = phone_obj.get_metadata("verification_code")
        expiry_str = phone_obj.get_metadata("verification_expiry")

        if not stored_code or not expiry_str:
            return False

        expiry = datetime.fromisoformat(expiry_str)
        if timezone.now() > expiry:
            logger.warning("Verification code expired for phone: %s", phone_obj.value)
            return False

        if stored_code != code:
            return False

        phone_obj.verify()
        phone_obj.remove_metadata("verification_code")
        phone_obj.remove_metadata("verification_expiry")

        logger.info("Phone verified via code: %s", phone_obj.value)
        return True
