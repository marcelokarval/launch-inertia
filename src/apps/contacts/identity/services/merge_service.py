"""
Identity merge service.

Handles the merge workflow: validation, relationship transfer,
signal dispatch, and history tracking.

Ported from legacy identity/services/merge_service.py.
"""

import logging
from datetime import timedelta
from typing import Any, Optional

from django.db import transaction
from django.db.models import Q
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
        - CaptureEvent tracking events
        - CaptureSubmission fact records

        Returns:
            Stats dict with counts of transferred records.
        """
        stats = {
            "emails_transferred": 0,
            "phones_transferred": 0,
            "fingerprints_transferred": 0,
            "events_transferred": 0,
            "submissions_transferred": 0,
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

        # Transfer tracking events (CaptureEvent)
        from core.tracking.models import CaptureEvent

        events = CaptureEvent.objects.filter(identity=source)
        stats["events_transferred"] = events.count()
        events.update(identity=target)

        # Transfer capture submissions (CaptureSubmission)
        from apps.ads.models import CaptureSubmission

        submissions = CaptureSubmission.objects.filter(identity=source)
        stats["submissions_transferred"] = submissions.count()
        submissions.update(identity=target)

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
        - IP + same OS within 7d (confidence 0.65) — same person, different browser
        - IP + different OS within 24h (confidence 0.3) — household, flag only

        Returns:
            List of dicts with candidate identity and confidence score.
        """
        candidates: dict[int, dict[str, Any]] = {}

        # ── Shared emails (0.9) ──────────────────────────────────────
        email_values = identity.email_contacts.values_list("value", flat=True)
        if email_values:
            from apps.contacts.email.models import ContactEmail

            shared_emails = ContactEmail.objects.filter(
                value__in=email_values,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for email in shared_emails:
                assert (
                    email.identity_id is not None
                )  # filtered by identity__isnull=False
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

        # ── Shared phones (0.8) ──────────────────────────────────────
        phone_values = identity.phone_contacts.values_list("value", flat=True)
        if phone_values:
            from apps.contacts.phone.models import ContactPhone

            shared_phones = ContactPhone.objects.filter(
                value__in=phone_values,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for phone in shared_phones:
                assert (
                    phone.identity_id is not None
                )  # filtered by identity__isnull=False
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

        # ── Shared fingerprints (0.7) ────────────────────────────────
        fp_hashes = identity.fingerprints.values_list("hash", flat=True)
        if fp_hashes:
            from apps.contacts.fingerprint.models import FingerprintIdentity

            shared_fps = FingerprintIdentity.objects.filter(
                hash__in=fp_hashes,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
            ).exclude(identity=identity)

            for fp in shared_fps:
                assert fp.identity_id is not None  # filtered by identity__isnull=False
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

        # ── IP + OS heuristics (0.65 same-person / 0.3 household) ───
        ip_candidates = MergeService._find_ip_os_candidates(identity)
        for ic in ip_candidates:
            candidate_id = ic["identity_id"]
            if (
                candidate_id not in candidates
                or candidates[candidate_id]["confidence"] < ic["confidence"]
            ):
                candidates[candidate_id] = ic

        return sorted(candidates.values(), key=lambda x: -x["confidence"])

    # ── IP + OS Heuristics ────────────────────────────────────────────

    @staticmethod
    def _find_ip_os_candidates(identity: Identity) -> list[dict[str, Any]]:
        """Find merge candidates via IP + OS heuristics.

        Queries CaptureEvents to find other identities that share the same
        IP address. Two sub-heuristics:

        1. **Same-person** (confidence 0.65):
           Same IP + same os_family (via DeviceProfile) within 7 days.
           Scenario: same person, different browser (e.g., Safari + Chrome on Mac).

        2. **Household** (confidence 0.3):
           Same IP + different os_family/device_type within 24 hours.
           Scenario: family members on the same network.
           Flag only — NOT eligible for auto-merge.

        Returns:
            List of candidate dicts (may be empty).
        """
        from core.tracking.models import CaptureEvent

        results: list[dict[str, Any]] = []
        now = timezone.now()

        # Get recent IPs for this identity (7-day window)
        identity_events = (
            CaptureEvent.objects.filter(
                identity=identity,
                ip_address__isnull=False,
                created_at__gte=now - timedelta(days=7),
            )
            .exclude(ip_address="")
            .values_list("ip_address", "device_profile_id")
            .distinct()
        )

        if not identity_events:
            return results

        # Collect IPs and device profiles for this identity
        identity_ips: set[str] = set()
        identity_device_pks: set[int] = set()
        for ip, dp_id in identity_events:
            if ip:
                identity_ips.add(ip)
            if dp_id:
                identity_device_pks.add(dp_id)

        if not identity_ips:
            return results

        # Get OS families for identity's device profiles
        from core.tracking.models import DeviceProfile

        identity_os_families: set[str] = set()
        if identity_device_pks:
            identity_os_families = set(
                DeviceProfile.objects.filter(pk__in=identity_device_pks).values_list(
                    "os_family", flat=True
                )
            )

        # Find other identities at the same IPs (7-day window)
        other_events = (
            CaptureEvent.objects.filter(
                ip_address__in=identity_ips,
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
                created_at__gte=now - timedelta(days=7),
            )
            .exclude(identity=identity)
            .values_list("identity_id", "ip_address", "device_profile_id", "created_at")
        )

        if not other_events:
            return results

        # Collect device profile PKs from other events for batch lookup
        other_dp_pks: set[int] = set()
        for _, _, dp_id, _ in other_events:
            if dp_id:
                other_dp_pks.add(dp_id)

        # Batch load OS families for other device profiles
        other_dp_os: dict[int, str] = {}
        if other_dp_pks:
            other_dp_os = dict(
                DeviceProfile.objects.filter(pk__in=other_dp_pks).values_list(
                    "pk", "os_family"
                )
            )

        # Group by candidate identity
        candidate_data: dict[int, dict[str, Any]] = {}
        for cand_identity_id, ip, dp_id, event_created_at in other_events:
            if cand_identity_id not in candidate_data:
                candidate_data[cand_identity_id] = {
                    "os_families": set(),
                    "ips": set(),
                    "recent_24h": False,
                }
            cd = candidate_data[cand_identity_id]
            cd["ips"].add(ip)
            if dp_id and dp_id in other_dp_os:
                cd["os_families"].add(other_dp_os[dp_id])
            if event_created_at >= now - timedelta(hours=24):
                cd["recent_24h"] = True

        # Score each candidate
        for cand_id, cd in candidate_data.items():
            shared_os = identity_os_families & cd["os_families"]

            if shared_os:
                # Same IP + same OS → same person, different browser (0.65)
                results.append(
                    {
                        "identity_id": cand_id,
                        "identity": None,  # Lazy-loaded below
                        "confidence": 0.65,
                        "match_type": "ip_same_os",
                        "match_value": f"IP overlap, OS: {', '.join(shared_os)}",
                    }
                )
            elif cd["recent_24h"] and cd["os_families"]:
                # Same IP + different OS within 24h → household (0.3)
                results.append(
                    {
                        "identity_id": cand_id,
                        "identity": None,  # Lazy-loaded below
                        "confidence": 0.3,
                        "match_type": "ip_household",
                        "match_value": f"IP overlap, different OS within 24h",
                    }
                )

        # Lazy-load Identity objects for results
        if results:
            cand_ids = [r["identity_id"] for r in results]
            identities_map = {
                i.pk: i
                for i in Identity.objects.filter(
                    pk__in=cand_ids, status=Identity.ACTIVE, is_deleted=False
                )
            }
            # Filter out candidates whose identity no longer exists
            valid_results = []
            for r in results:
                identity_obj = identities_map.get(r["identity_id"])
                if identity_obj:
                    r["identity"] = identity_obj
                    valid_results.append(r)
            return valid_results

        return results

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
