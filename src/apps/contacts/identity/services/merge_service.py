"""
Identity merge service.

Handles the merge workflow: validation, relationship transfer,
signal dispatch, and history tracking.

Ported from legacy identity/services/merge_service.py.
"""

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.contacts.identity.models import Identity, IdentityHistory

logger = logging.getLogger(__name__)


class MergeValidationError(Exception):
    """Raised when merge preconditions are not met."""

    pass


class MergeService:
    """Service for merging identities."""

    # ── Validation ───────────────────────────────────────────────────

    @staticmethod
    def validate_merge_conditions(source: Identity, target: Identity) -> None:
        """
        Validate that a merge can be performed.

        Raises MergeValidationError if:
        - Source and target are the same identity
        - Source is not ACTIVE
        - Target is not ACTIVE
        - Source is already merged
        """
        if source.pk == target.pk:
            raise MergeValidationError("Cannot merge an identity into itself")

        if source.status != Identity.ACTIVE:
            raise MergeValidationError(
                f"Source identity {source.public_id} is not active (status: {source.status})"
            )

        if target.status != Identity.ACTIVE:
            raise MergeValidationError(
                f"Target identity {target.public_id} is not active (status: {target.status})"
            )

        if source.merged_into is not None:
            raise MergeValidationError(
                f"Source identity {source.public_id} is already merged into {source.merged_into.public_id}"
            )

    # ── Relationship Transfer ────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def transfer_relationships(source: Identity, target: Identity) -> dict:
        """
        Transfer all relationships from source to target identity.

        Moves:
        - ContactEmail records
        - ContactPhone records
        - FingerprintIdentity records

        Returns:
            Stats dict with counts of transferred records.
        """
        stats = {
            "emails_transferred": 0,
            "phones_transferred": 0,
            "fingerprints_transferred": 0,
        }

        # Transfer emails
        emails = source.email_contacts.all()
        stats["emails_transferred"] = emails.count()
        emails.update(identity=target)

        # Transfer phones
        phones = source.phone_contacts.all()
        stats["phones_transferred"] = phones.count()
        phones.update(identity=target)

        # Transfer fingerprints
        fingerprints = source.fingerprints.all()
        stats["fingerprints_transferred"] = fingerprints.count()
        fingerprints.update(identity=target)

        return stats

    # ── Execute Merge ────────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def execute_merge(cls, source: Identity, target: Identity) -> dict:
        """
        Execute a full identity merge.

        Steps:
        1. Validate preconditions
        2. Fire pre-merge signal
        3. Transfer all relationships
        4. Mark source as MERGED
        5. Update history for both
        6. Fire post-merge signal
        7. Update target last_seen

        Args:
            source: Identity to merge FROM (will be deactivated).
            target: Identity to merge INTO (will receive all data).

        Returns:
            Dict with merge statistics.

        Raises:
            MergeValidationError: If preconditions fail.
        """
        # 1. Validate
        cls.validate_merge_conditions(source, target)

        # 2. Pre-merge signal
        from apps.contacts.identity.signals_def import identity_pre_merge

        identity_pre_merge.send(
            sender=source.__class__,
            source=source,
            target=target,
        )

        # 3. Transfer relationships
        stats = cls.transfer_relationships(source, target)

        # 4. Mark source as merged
        source.mark_as_merged(target)

        # 5. Update history
        IdentityHistory.objects.create(
            identity=source,
            operation_type=IdentityHistory.MERGE,
            details={
                "merged_into": target.public_id,
                "stats": stats,
            },
        )
        IdentityHistory.objects.create(
            identity=target,
            operation_type=IdentityHistory.MERGE,
            details={
                "absorbed": source.public_id,
                "stats": stats,
            },
        )

        # 6. Post-merge signal
        from apps.contacts.identity.signals_def import identity_post_merge

        identity_post_merge.send(
            sender=source.__class__,
            source=source,
            target=target,
            stats=stats,
        )

        # 7. Update target
        target.update_last_seen()

        logger.info(
            "Merged identity %s into %s (emails=%d, phones=%d, fps=%d)",
            source.public_id,
            target.public_id,
            stats["emails_transferred"],
            stats["phones_transferred"],
            stats["fingerprints_transferred"],
        )

        return stats

    # ── Merge Candidate Discovery ────────────────────────────────────

    @staticmethod
    def find_merge_candidates(identity: Identity) -> list[dict]:
        """
        Find identities that might be the same person.

        Searches for shared:
        - Email addresses (confidence 0.9)
        - Phone numbers (confidence 0.8)
        - Fingerprints (confidence 0.7)

        Returns:
            List of dicts with candidate identity and confidence score.
        """
        candidates = {}

        # Shared emails
        email_values = identity.email_contacts.values_list("value", flat=True)
        if email_values:
            from apps.contacts.email.models import ContactEmail

            shared_emails = ContactEmail.objects.filter(
                value__in=email_values,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for email in shared_emails:
                candidate_id = email.identity_id
                if (
                    candidate_id not in candidates
                    or candidates[candidate_id]["confidence"] < 0.9
                ):
                    candidates[candidate_id] = {
                        "identity_id": candidate_id,
                        "identity": email.identity,
                        "confidence": 0.9,
                        "match_type": "email",
                        "match_value": email.value,
                    }

        # Shared phones
        phone_values = identity.phone_contacts.values_list("value", flat=True)
        if phone_values:
            from apps.contacts.phone.models import ContactPhone

            shared_phones = ContactPhone.objects.filter(
                value__in=phone_values,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for phone in shared_phones:
                candidate_id = phone.identity_id
                if (
                    candidate_id not in candidates
                    or candidates[candidate_id]["confidence"] < 0.8
                ):
                    candidates[candidate_id] = {
                        "identity_id": candidate_id,
                        "identity": phone.identity,
                        "confidence": 0.8,
                        "match_type": "phone",
                        "match_value": phone.value,
                    }

        # Shared fingerprints
        fp_hashes = identity.fingerprints.values_list("hash", flat=True)
        if fp_hashes:
            from apps.contacts.fingerprint.models import FingerprintIdentity

            shared_fps = FingerprintIdentity.objects.filter(
                hash__in=fp_hashes,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for fp in shared_fps:
                candidate_id = fp.identity_id
                if (
                    candidate_id not in candidates
                    or candidates[candidate_id]["confidence"] < 0.7
                ):
                    candidates[candidate_id] = {
                        "identity_id": candidate_id,
                        "identity": fp.identity,
                        "confidence": 0.7,
                        "match_type": "fingerprint",
                        "match_value": fp.hash[:12],
                    }

        return sorted(candidates.values(), key=lambda x: -x["confidence"])

    # ── Auto-Merge ───────────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def auto_merge_identities(cls, identity: Identity) -> list[dict]:
        """
        Automatically merge high-confidence candidates into this identity.

        Only merges candidates with confidence >= 0.9.
        Merges oldest-first to preserve the oldest identity as master.

        Returns:
            List of merge result dicts.
        """
        candidates = cls.find_merge_candidates(identity)
        high_confidence = [c for c in candidates if c["confidence"] >= 0.9]

        results = []
        for candidate in high_confidence:
            candidate_identity = candidate["identity"]
            try:
                # Merge the candidate into our identity (oldest survives)
                if candidate_identity.created_at < identity.created_at:
                    # Candidate is older, merge us into them
                    stats = cls.execute_merge(identity, candidate_identity)
                    results.append(
                        {
                            "merged": identity.public_id,
                            "into": candidate_identity.public_id,
                            "stats": stats,
                        }
                    )
                    break  # Our identity is now merged, stop
                else:
                    stats = cls.execute_merge(candidate_identity, identity)
                    results.append(
                        {
                            "merged": candidate_identity.public_id,
                            "into": identity.public_id,
                            "stats": stats,
                        }
                    )
            except MergeValidationError as e:
                logger.warning("Auto-merge skipped: %s", str(e))

        return results
