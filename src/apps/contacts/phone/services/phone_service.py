"""
Phone contact service.

Handles CRUD operations for ContactPhone records.
Ported from legacy contact/services/phone_service.py,
adapted to use BaseService[ContactPhone] pattern.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from django.db import transaction
from django.utils import timezone

from core.shared.services.base import BaseService
from apps.contacts.phone.models import ContactPhone

logger = logging.getLogger(__name__)


class PhoneService(BaseService[ContactPhone]):
    """Service for managing contact phone records."""

    model = ContactPhone

    # ── Get or Create ────────────────────────────────────────────────

    @transaction.atomic
    def get_or_create_phone(
        self,
        phone_value: str,
        original_value: str | None = None,
        country_code: str | None = None,
    ) -> tuple[ContactPhone, bool]:
        """
        Get or create a ContactPhone by normalized value.

        Args:
            phone_value: The phone number to find/create.
            original_value: The raw input before normalization.
            country_code: Country code (default: "55" for Brazil).

        Returns:
            Tuple of (ContactPhone, created: bool)
        """
        # Normalize: create a temporary instance to use the model's normalize()
        temp = ContactPhone(value=phone_value, country_code=country_code or "55")
        temp.normalize()
        normalized = temp.value

        phone_obj, created = ContactPhone.objects.get_or_create(
            value=normalized,
            defaults={
                "original_value": original_value or phone_value,
                "country_code": country_code or "55",
            },
        )

        if not created:
            phone_obj.last_seen = timezone.now()
            phone_obj.save(update_fields=["last_seen", "updated_at"])

        logger.info(
            "%s phone: %s",
            "Created" if created else "Found",
            normalized,
        )
        return phone_obj, created

    # ── Verification ─────────────────────────────────────────────────

    def verify_phone(self, phone_obj: ContactPhone) -> ContactPhone:
        """Mark a phone as verified with timestamp."""
        phone_obj.verify()
        logger.info("Verified phone: %s", phone_obj.value)
        return phone_obj

    def unverify_phone(self, phone_obj: ContactPhone) -> ContactPhone:
        """Remove verification from a phone."""
        phone_obj.unverify()
        logger.info("Unverified phone: %s", phone_obj.value)
        return phone_obj

    # ── Lookups ──────────────────────────────────────────────────────

    def get_phone_by_value(
        self,
        phone_value: str,
        country_code: str | None = None,
    ) -> Optional[ContactPhone]:
        """Find a ContactPhone by its normalized value."""
        temp = ContactPhone(value=phone_value, country_code=country_code or "55")
        temp.normalize()
        return ContactPhone.objects.filter(value=temp.value).first()

    def get_phones_for_identity(self, identity_id: int) -> list[ContactPhone]:
        """Get all phones linked to a specific identity."""
        return list(ContactPhone.objects.filter(identity_id=identity_id))

    # ── Normalization ────────────────────────────────────────────────

    @staticmethod
    def normalize_phone(phone_value: str, country_code: str | None = None) -> str:
        """
        Normalize a phone number to a consistent format.

        Strips non-digits, prepends country code if missing.
        """
        digits = re.sub(r"[^\d]", "", phone_value)
        cc = country_code or "55"
        if digits and not digits.startswith(cc):
            digits = f"{cc}{digits}"
        return f"+{digits}" if digits else phone_value

    @staticmethod
    def format_phone_for_display(phone_value: str) -> str:
        """
        Format phone for Brazilian display.

        Returns: (XX) XXXXX-XXXX or (XX) XXXX-XXXX
        """
        digits = re.sub(r"[^\d]", "", phone_value)
        if digits.startswith("55"):
            digits = digits[2:]

        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return phone_value

    @staticmethod
    def detect_phone_type(phone_value: str) -> str:
        """
        Detect phone type based on Brazilian numbering patterns.

        Returns: "mobile", "landline", or "unknown"
        """
        digits = re.sub(r"[^\d]", "", phone_value)
        if digits.startswith("55"):
            digits = digits[2:]

        if len(digits) == 11 and digits[2] == "9":
            return "mobile"
        elif len(digits) == 10:
            return "landline"
        return "unknown"
