"""
Identity resolution service.

The core algorithm that resolves incoming fingerprint + contact data
into a unified Identity. This is the "crown jewel" of the contact system.

Pipeline:
1. Get/create FingerprintIdentity from visitorId
2. If no contacts: create/get anonymous identity
3. If contacts exist: find existing identities by email/phone
4. If no existing: create new identity with contacts
5. If one existing: associate fingerprint to it
6. If multiple existing: merge into oldest

Ported from legacy identity/services/resolution_service.py.
"""

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.contacts.identity.models import Identity, IdentityHistory

logger = logging.getLogger(__name__)


class ResolutionService:
    """
    Resolves fingerprint + contact data into a unified Identity.
    """

    # ── Main Resolution Entry Point ──────────────────────────────────

    @classmethod
    @transaction.atomic
    def resolve_identity_from_real_data(
        cls,
        fingerprint_data: dict,
        contact_data: Optional[dict] = None,
    ) -> dict:
        """
        Main entry point for identity resolution.

        Args:
            fingerprint_data: Dict with at minimum {"hash": "visitor_id"}.
            contact_data: Optional dict with {"email": "...", "phone": "..."}.

        Returns:
            Dict with identity_id, fingerprint_id, is_new, confidence_score.
        """
        # Step 1: Get/create fingerprint
        fingerprint, fp_created = cls.get_or_create_fingerprint_identity(
            fingerprint_data
        )

        # Step 2: No contacts -> anonymous identity
        if not contact_data or (
            not contact_data.get("email") and not contact_data.get("phone")
        ):
            identity = cls.create_or_get_anonymous_identity(fingerprint)
            return {
                "identity_id": identity.public_id,
                "fingerprint_id": fingerprint.public_id,
                "is_new": fp_created,
                "is_anonymous": True,
                "confidence_score": identity.confidence_score,
            }

        # Step 3: Find existing identities by contact data
        existing_identities = cls.find_existing_identities(contact_data)

        if len(existing_identities) == 0:
            # Step 4a: No existing -> create new identity
            identity = cls.create_new_identity_with_contacts(fingerprint, contact_data)
            return {
                "identity_id": identity.public_id,
                "fingerprint_id": fingerprint.public_id,
                "is_new": True,
                "is_anonymous": False,
                "confidence_score": identity.confidence_score,
            }

        elif len(existing_identities) == 1:
            # Step 4b: One existing -> associate
            identity = cls.associate_fingerprint_to_identity(
                fingerprint, existing_identities[0], contact_data
            )
            return {
                "identity_id": identity.public_id,
                "fingerprint_id": fingerprint.public_id,
                "is_new": False,
                "is_anonymous": False,
                "confidence_score": identity.confidence_score,
            }

        else:
            # Step 4c: Multiple existing -> merge
            identity = cls.merge_multiple_identities(
                fingerprint, existing_identities, contact_data
            )
            return {
                "identity_id": identity.public_id,
                "fingerprint_id": fingerprint.public_id,
                "is_new": False,
                "is_anonymous": False,
                "confidence_score": identity.confidence_score,
                "merged_count": len(existing_identities) - 1,
            }

    # ── Fingerprint Handling ─────────────────────────────────────────

    @staticmethod
    def get_or_create_fingerprint_identity(fingerprint_data: dict):
        """Get or create a FingerprintIdentity from hash."""
        from apps.contacts.fingerprint.services.fingerprint_service import (
            FingerprintService,
        )

        service = FingerprintService()
        return service.get_or_create_fingerprint(fingerprint_data)

    # ── Identity Finding ─────────────────────────────────────────────

    @staticmethod
    def find_existing_identities(contact_data: dict) -> list[Identity]:
        """
        Search for existing active identities by email and phone.

        Returns deduplicated list of Identity objects.
        """
        identity_ids = set()
        identities = []

        # Search by email
        email = contact_data.get("email")
        if email:
            from apps.contacts.email.models import ContactEmail

            email_obj = (
                ContactEmail.objects.filter(
                    value=email.lower().strip(),
                    identity__isnull=False,
                    identity__status=Identity.ACTIVE,
                )
                .select_related("identity")
                .first()
            )

            if email_obj and email_obj.identity_id not in identity_ids:
                identity_ids.add(email_obj.identity_id)
                identities.append(email_obj.identity)

        # Search by phone
        phone = contact_data.get("phone")
        if phone:
            from apps.contacts.phone.models import ContactPhone

            # Try both normalized and raw
            import re

            digits = re.sub(r"[^\d]", "", phone)
            phone_queries = [phone]
            if digits:
                phone_queries.append(f"+{digits}")
                if not digits.startswith("55"):
                    phone_queries.append(f"+55{digits}")

            phone_obj = (
                ContactPhone.objects.filter(
                    value__in=phone_queries,
                    identity__isnull=False,
                    identity__status=Identity.ACTIVE,
                )
                .select_related("identity")
                .first()
            )

            if phone_obj and phone_obj.identity_id not in identity_ids:
                identity_ids.add(phone_obj.identity_id)
                identities.append(phone_obj.identity)

        return identities

    # ── Anonymous Identity ───────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_or_get_anonymous_identity(fingerprint) -> Identity:
        """
        Create or retrieve an anonymous identity for a fingerprint-only visitor.
        """
        if fingerprint.identity:
            return fingerprint.identity

        # Create new anonymous identity
        identity = Identity.objects.create(
            status=Identity.ACTIVE,
            first_seen_source="fingerprint",
            last_seen=timezone.now(),
        )

        fingerprint.identity = identity
        fingerprint.save(update_fields=["identity", "updated_at"])

        IdentityHistory.objects.create(
            identity=identity,
            operation_type=IdentityHistory.UPDATE,
            details={
                "action": "anonymous_identity_created",
                "fingerprint_hash": fingerprint.hash[:12],
            },
        )

        logger.info(
            "Created anonymous identity %s for fingerprint %s",
            identity.public_id,
            fingerprint.hash[:12],
        )
        return identity

    # ── New Identity with Contacts ───────────────────────────────────

    @classmethod
    @transaction.atomic
    def create_new_identity_with_contacts(
        cls,
        fingerprint,
        contact_data: dict,
    ) -> Identity:
        """
        Create a new Identity and associate contacts + fingerprint.
        """
        identity = Identity.objects.create(
            status=Identity.ACTIVE,
            first_seen_source="form",
            last_seen=timezone.now(),
            confidence_score=cls.calculate_initial_confidence_score(
                fingerprint, contact_data
            ),
        )

        # Link fingerprint
        fingerprint.identity = identity
        fingerprint.is_master = True
        fingerprint.save(update_fields=["identity", "is_master", "updated_at"])

        # Create/link email
        if contact_data.get("email"):
            from apps.contacts.email.services.email_service import EmailService

            email_service = EmailService()
            email_obj, _ = email_service.get_or_create_email(contact_data["email"])
            email_obj.identity = identity
            email_obj.save(update_fields=["identity", "updated_at"])

            IdentityHistory.objects.create(
                identity=identity,
                operation_type=IdentityHistory.CONTACT_ADDED,
                details={"type": "email", "value": email_obj.value},
            )

        # Create/link phone
        if contact_data.get("phone"):
            from apps.contacts.phone.services.phone_service import PhoneService

            phone_service = PhoneService()
            phone_obj, _ = phone_service.get_or_create_phone(contact_data["phone"])
            phone_obj.identity = identity
            phone_obj.save(update_fields=["identity", "updated_at"])

            IdentityHistory.objects.create(
                identity=identity,
                operation_type=IdentityHistory.CONTACT_ADDED,
                details={"type": "phone", "value": phone_obj.value},
            )

        # History
        IdentityHistory.objects.create(
            identity=identity,
            operation_type=IdentityHistory.UPDATE,
            details={
                "action": "identity_created_with_contacts",
                "fingerprint": fingerprint.hash[:12],
                "has_email": bool(contact_data.get("email")),
                "has_phone": bool(contact_data.get("phone")),
            },
        )

        # Signal
        from apps.contacts.identity.signals_def import identity_created

        identity_created.send(
            sender=Identity,
            instance=identity,
            source="form",
        )

        logger.info("Created identity %s with contacts", identity.public_id)
        return identity

    # ── Associate Fingerprint to Existing ────────────────────────────

    @classmethod
    @transaction.atomic
    def associate_fingerprint_to_identity(
        cls,
        fingerprint,
        existing_identity: Identity,
        contact_data: dict,
    ) -> Identity:
        """
        Associate a fingerprint to an existing identity and add any new contacts.
        """
        # Link fingerprint
        fingerprint.identity = existing_identity

        # Determine if this should be master fingerprint
        existing_fps = existing_identity.fingerprints.count()
        if existing_fps == 0:
            fingerprint.is_master = True

        fingerprint.save(update_fields=["identity", "is_master", "updated_at"])

        IdentityHistory.objects.create(
            identity=existing_identity,
            operation_type=IdentityHistory.FINGERPRINT_LINKED,
            details={"fingerprint_hash": fingerprint.hash[:12]},
        )

        # Add new contacts if they don't exist on this identity
        if contact_data.get("email"):
            from apps.contacts.email.services.email_service import EmailService

            email_service = EmailService()
            email_obj, _ = email_service.get_or_create_email(contact_data["email"])
            if not email_obj.identity:
                email_obj.identity = existing_identity
                email_obj.save(update_fields=["identity", "updated_at"])

        if contact_data.get("phone"):
            from apps.contacts.phone.services.phone_service import PhoneService

            phone_service = PhoneService()
            phone_obj, _ = phone_service.get_or_create_phone(contact_data["phone"])
            if not phone_obj.identity:
                phone_obj.identity = existing_identity
                phone_obj.save(update_fields=["identity", "updated_at"])

        # Update confidence and last_seen
        existing_identity.confidence_score = cls.calculate_real_confidence_score(
            existing_identity
        )
        existing_identity.last_seen = timezone.now()
        existing_identity.save(
            update_fields=["confidence_score", "last_seen", "updated_at"]
        )

        logger.info(
            "Associated fingerprint %s to identity %s",
            fingerprint.hash[:12],
            existing_identity.public_id,
        )
        return existing_identity

    # ── Merge Multiple Identities ────────────────────────────────────

    @classmethod
    @transaction.atomic
    def merge_multiple_identities(
        cls,
        fingerprint,
        identities: list[Identity],
        contact_data: dict,
    ) -> Identity:
        """
        When multiple identities are found, merge them into the oldest one.
        """
        from apps.contacts.identity.services.merge_service import MergeService

        # Find the oldest (master) identity
        master = min(identities, key=lambda i: i.created_at)
        others = [i for i in identities if i.pk != master.pk]

        # Merge all others into master
        for other in others:
            try:
                MergeService.execute_merge(other, master)
            except Exception as e:
                logger.error(
                    "Failed to merge %s into %s: %s",
                    other.public_id,
                    master.public_id,
                    str(e),
                )

        # Associate the fingerprint
        cls.associate_fingerprint_to_identity(fingerprint, master, contact_data)

        logger.info(
            "Merged %d identities into master %s",
            len(others),
            master.public_id,
        )
        return master

    # ── Confidence Scoring ───────────────────────────────────────────

    @staticmethod
    def calculate_real_confidence_score(identity: Identity) -> float:
        """
        Full confidence recalculation for an existing identity.

        Delegates to ConfidenceEngine.calculate() which considers:
        - FingerprintJS confidence averages
        - Verified/unverified email/phone bonuses
        - Cross-device bonuses
        - Fraud penalties (incognito, VPN)
        - Contact quality penalties (bounced, DNC)
        """
        from apps.contacts.identity.services.confidence_engine import ConfidenceEngine

        return ConfidenceEngine.calculate(identity)

    @staticmethod
    def calculate_initial_confidence_score(fingerprint, contact_data: dict) -> float:
        """
        Fast confidence estimate for a newly created identity.

        Delegates to ConfidenceEngine.calculate_initial().
        """
        from apps.contacts.identity.services.confidence_engine import ConfidenceEngine

        return ConfidenceEngine.calculate_initial(
            fingerprint_confidence=fingerprint.confidence_score or 0.3,
            has_email=bool(contact_data.get("email")),
            has_phone=bool(contact_data.get("phone")),
        )
