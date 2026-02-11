"""
Event processing service.

Handles the main event ingestion pipeline:
fingerprint payload -> event recording -> contact association -> identity resolution.

Ported from legacy fingerprint/services/event_service.py.
"""

import logging
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from apps.contacts.fingerprint.models import (
    FingerprintContact,
    FingerprintEvent,
    FingerprintIdentity,
)

logger = logging.getLogger(__name__)


class EventService:
    """
    Processes incoming events and manages fingerprint-contact associations.
    """

    # ── Contact Processing ───────────────────────────────────────────

    @staticmethod
    def process_contacts(contact_data: dict) -> list[tuple]:
        """
        Get or create ContactEmail/ContactPhone from contact data.

        Args:
            contact_data: Dict with optional "email" and "phone" keys.

        Returns:
            List of (contact_object, content_type) tuples.
        """
        contacts = []

        if contact_data.get("email"):
            from apps.contacts.email.services.email_service import EmailService

            email_service = EmailService()
            email_obj, _ = email_service.get_or_create_email(contact_data["email"])
            ct = ContentType.objects.get_for_model(email_obj)
            contacts.append((email_obj, ct))

        if contact_data.get("phone"):
            from apps.contacts.phone.services.phone_service import PhoneService

            phone_service = PhoneService()
            phone_obj, _ = phone_service.get_or_create_phone(contact_data["phone"])
            ct = ContentType.objects.get_for_model(phone_obj)
            contacts.append((phone_obj, ct))

        return contacts

    # ── Contact-Fingerprint Association ──────────────────────────────

    @staticmethod
    @transaction.atomic
    def associate_contacts_with_fingerprint(
        fingerprint: FingerprintIdentity,
        contacts: list[tuple],
    ) -> list[FingerprintContact]:
        """
        Create or update FingerprintContact associations.

        Args:
            fingerprint: The FingerprintIdentity to link to.
            contacts: List of (contact_object, content_type) tuples.

        Returns:
            List of FingerprintContact records.
        """
        associations = []

        for contact_obj, content_type in contacts:
            fp_contact, created = FingerprintContact.objects.get_or_create(
                fingerprint=fingerprint,
                content_type=content_type,
                object_id=contact_obj.pk,
                defaults={
                    "verification_status": FingerprintContact.UNVERIFIED,
                },
            )

            if not created:
                fp_contact.last_seen = timezone.now()
                fp_contact.save(update_fields=["last_seen", "updated_at"])

            associations.append(fp_contact)

        return associations

    # ── Event Recording ──────────────────────────────────────────────

    @staticmethod
    def register_event(
        fingerprint: FingerprintIdentity,
        data: dict,
    ) -> FingerprintEvent:
        """
        Create a FingerprintEvent record.

        Args:
            fingerprint: The fingerprint that generated this event.
            data: Dict with event_type, page_url, user_data, event_data, session_id.
        """
        return FingerprintEvent.objects.create(
            fingerprint=fingerprint,
            event_type=data.get("event_type", "unknown"),
            page_url=data.get("page_url"),
            timestamp=data.get("timestamp", timezone.now()),
            user_data=data.get("user_data", {}),
            event_data=data.get("event_data", {}),
            session_id=data.get("session_id"),
        )

    # ── Main Event Processing Pipeline ───────────────────────────────

    @classmethod
    @transaction.atomic
    def process_event(cls, event_data: dict) -> dict:
        """
        Main entry point for processing incoming events.

        This is the core pipeline:
        1. Parse fingerprint data from payload
        2. Get/create FingerprintIdentity
        3. Process contacts (email/phone) if present
        4. Associate contacts with fingerprint
        5. Record the event
        6. Trigger identity resolution

        Args:
            event_data: Raw event payload (from FingerprintJS Pro or legacy format).

        Returns:
            Dict with processing results.
        """
        from apps.contacts.fingerprint.services.payload_service import PayloadService

        # Detect format and parse
        if "requestId" in event_data or "visitorId" in event_data:
            # FingerprintJS Pro format
            fingerprint_data, context_data = (
                PayloadService.process_fingerprintjs_payload(event_data)
            )
        else:
            # Legacy format
            fingerprint_data = {
                "hash": event_data.get("fingerprint", event_data.get("visitor_id", "")),
                "device_type": event_data.get("device_type", "unknown"),
            }
            context_data = event_data

        if not fingerprint_data.get("hash"):
            logger.error("No fingerprint hash in event data")
            return {"error": "Missing fingerprint hash"}

        # Get or create fingerprint
        from apps.contacts.fingerprint.services.fingerprint_service import (
            FingerprintService,
        )

        fp_service = FingerprintService()
        fingerprint, fp_created = fp_service.get_or_create_fingerprint(fingerprint_data)

        if not fp_created:
            fingerprint.update_from_payload(fingerprint_data)

        # Process contacts
        contact_data = context_data.get("contact_data", {})
        contacts = cls.process_contacts(contact_data) if contact_data else []

        # Associate contacts with fingerprint
        if contacts:
            cls.associate_contacts_with_fingerprint(fingerprint, contacts)

        # Record event
        event = cls.register_event(
            fingerprint,
            {
                "event_type": context_data.get("event_type", "page_view"),
                "page_url": context_data.get("page_url"),
                "user_data": context_data.get("user_data", {}),
                "event_data": context_data.get("event_data", {}),
                "session_id": context_data.get("session_id"),
            },
        )

        # Trigger identity resolution
        from apps.contacts.identity.services.resolution_service import ResolutionService

        resolution_result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data=fingerprint_data,
            contact_data=contact_data if contact_data else None,
        )

        return {
            "fingerprint_id": fingerprint.public_id,
            "fingerprint_created": fp_created,
            "event_id": event.public_id,
            "contacts_processed": len(contacts),
            "identity_id": resolution_result.get("identity_id"),
        }

    # ── Event Retrieval ──────────────────────────────────────────────

    @staticmethod
    def get_events_for_fingerprint(
        fingerprint: FingerprintIdentity,
        limit: int = 100,
    ) -> list[FingerprintEvent]:
        """
        Get events for a fingerprint, with fallback to identity-wide events.
        """
        events = list(fingerprint.events.order_by("-timestamp")[:limit])

        if not events and fingerprint.identity:
            # Fallback: get events across all fingerprints for this identity
            from apps.contacts.fingerprint.models import FingerprintEvent

            fp_ids = fingerprint.identity.fingerprints.values_list("id", flat=True)
            events = list(
                FingerprintEvent.objects.filter(fingerprint_id__in=fp_ids).order_by(
                    "-timestamp"
                )[:limit]
            )

        return events
