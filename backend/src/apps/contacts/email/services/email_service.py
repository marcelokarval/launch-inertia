"""
Email contact service.

Handles CRUD operations for ContactEmail records.
Ported from legacy contact/services/email_service.py,
adapted to use BaseService[ContactEmail] pattern.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from core.shared.services.base import BaseService
from apps.contacts.email.models import ContactEmail

logger = logging.getLogger(__name__)


class EmailService(BaseService[ContactEmail]):
    """Service for managing contact email records."""

    model = ContactEmail

    # ── Get or Create ────────────────────────────────────────────────

    @transaction.atomic
    def get_or_create_email(
        self,
        email_value: str,
        original_value: str | None = None,
    ) -> tuple[ContactEmail, bool]:
        """
        Get or create a ContactEmail by normalized value.

        Args:
            email_value: The email address to find/create.
            original_value: The raw input before normalization.

        Returns:
            Tuple of (ContactEmail, created: bool)
        """
        normalized = email_value.lower().strip()
        domain = ""
        if "@" in normalized:
            domain = normalized.split("@")[1]

        email_obj, created = ContactEmail.objects.get_or_create(
            value=normalized,
            defaults={
                "original_value": original_value or email_value,
                "domain": domain,
            },
        )

        if not created:
            # Update last_seen
            email_obj.last_seen = timezone.now()
            email_obj.save(update_fields=["last_seen", "updated_at"])

        logger.info(
            "%s email: %s",
            "Created" if created else "Found",
            normalized,
        )
        return email_obj, created

    # ── Verification ─────────────────────────────────────────────────

    def verify_email(self, email_obj: ContactEmail) -> ContactEmail:
        """Mark an email as verified with timestamp."""
        email_obj.verify()
        logger.info("Verified email: %s", email_obj.value)
        return email_obj

    def unverify_email(self, email_obj: ContactEmail) -> ContactEmail:
        """Remove verification from an email."""
        email_obj.unverify()
        logger.info("Unverified email: %s", email_obj.value)
        return email_obj

    # ── Bounce Processing ────────────────────────────────────────────

    def process_email_bounce(
        self,
        email_obj: ContactEmail,
        bounce_data: dict,
    ) -> ContactEmail:
        """
        Process an email bounce event.

        Marks the email as unverified and stores bounce details in metadata.

        Args:
            email_obj: The email that bounced.
            bounce_data: Bounce details from ESP (type, reason, timestamp, etc.)
        """
        email_obj.unverify()
        email_obj.update_metadata(
            {
                "bounce_data": bounce_data,
                "last_bounce_at": timezone.now().isoformat(),
            }
        )
        logger.warning("Email bounce processed: %s", email_obj.value)
        return email_obj

    # ── Lookups ──────────────────────────────────────────────────────

    def get_email_by_value(self, email_value: str) -> Optional[ContactEmail]:
        """Find a ContactEmail by its normalized value."""
        normalized = email_value.lower().strip()
        return ContactEmail.objects.filter(value=normalized).first()

    def get_emails_by_domain(self, domain: str) -> list[ContactEmail]:
        """Find all ContactEmails for a specific domain."""
        return list(ContactEmail.objects.filter(domain=domain.lower().strip()))

    def get_emails_for_identity(self, identity_id: int) -> list[ContactEmail]:
        """Get all emails linked to a specific identity."""
        return list(ContactEmail.objects.filter(identity_id=identity_id))

    # ── Domain Analysis ──────────────────────────────────────────────

    @staticmethod
    def extract_domain(email_value: str) -> str:
        """Extract domain from email address."""
        if "@" in email_value:
            return email_value.split("@")[1].lower().strip()
        return ""

    @staticmethod
    def is_disposable_email(email_value: str) -> bool:
        """Check if email uses a known disposable domain."""
        disposable_domains = {
            "tempmail.com",
            "throwaway.email",
            "guerrillamail.com",
            "mailinator.com",
            "yopmail.com",
            "tempinbox.com",
            "10minutemail.com",
            "trashmail.com",
            "fakeinbox.com",
            "sharklasers.com",
            "guerrillamailblock.com",
            "grr.la",
        }
        domain = EmailService.extract_domain(email_value)
        return domain in disposable_domains
