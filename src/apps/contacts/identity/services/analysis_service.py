"""
Identity analysis service.

Provides graph analysis, similarity detection, and comprehensive
identity profiling.

Ported from legacy identity/services/analysis_service.py.
"""

import logging
from typing import Optional

from django.utils import timezone

from apps.contacts.identity.models import Identity

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Analyzes identities for insights, similarity, and profiling.
    """

    # ── Comprehensive Analysis ───────────────────────────────────────

    @staticmethod
    def analyze_identity_graph(identity: Identity) -> dict:
        """
        Comprehensive analysis of an identity's data graph.

        Analyzes:
        - Contact counts (verified/unverified)
        - Device diversity (types, browsers, OSes)
        - Activity patterns (events, pages, sessions)
        - Relationships (merged identities)

        Stores results in identity's metadata and returns them.
        """
        # Contacts
        emails = identity.email_contacts.all()
        phones = identity.phone_contacts.all()
        verified_emails = sum(1 for e in emails if e.is_verified)
        verified_phones = sum(1 for p in phones if p.is_verified)

        # Devices
        fingerprints = identity.fingerprints.all()
        device_types = set()
        browsers = set()
        oses = set()
        for fp in fingerprints:
            device_types.add(fp.device_type)
            if fp.browser:
                browsers.add(fp.browser)
            if fp.os:
                oses.add(fp.os)

        # Activity
        from apps.contacts.fingerprint.models import FingerprintEvent

        fp_ids = list(fingerprints.values_list("id", flat=True))
        events = FingerprintEvent.objects.filter(fingerprint_id__in=fp_ids)
        event_types = set(events.values_list("event_type", flat=True))
        page_urls = set(events.values_list("page_url", flat=True).distinct()[:50])

        first_event = events.order_by("timestamp").first()
        last_event = events.order_by("-timestamp").first()

        # Relationships
        merged_count = identity.merged_identities.count()

        analysis = {
            "contacts": {
                "emails": {
                    "total": emails.count(),
                    "verified": verified_emails,
                    "unverified": emails.count() - verified_emails,
                },
                "phones": {
                    "total": phones.count(),
                    "verified": verified_phones,
                    "unverified": phones.count() - verified_phones,
                },
            },
            "devices": {
                "fingerprint_count": len(fp_ids),
                "device_types": list(device_types),
                "browsers": list(browsers),
                "operating_systems": list(oses),
            },
            "activity": {
                "total_events": events.count(),
                "event_types": list(event_types),
                "unique_pages": len(page_urls),
                "first_seen": first_event.timestamp.isoformat()
                if first_event
                else None,
                "last_seen": last_event.timestamp.isoformat() if last_event else None,
            },
            "relationships": {
                "merged_identities": merged_count,
            },
            "analyzed_at": timezone.now().isoformat(),
        }

        identity.update_metadata({"graph_analysis": analysis})
        logger.info("Analyzed identity graph: %s", identity.public_id)
        return analysis

    # ── Similarity Detection ─────────────────────────────────────────

    @staticmethod
    def find_similar_identities(identity: Identity) -> list[dict]:
        """
        Find identities similar to this one.

        Scoring:
        - Same email: +0.5
        - Same phone: +0.4
        - Same fingerprint: +0.3

        Returns:
            Sorted list of {identity, score, matches} dicts.
        """
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.phone.models import ContactPhone
        from apps.contacts.fingerprint.models import FingerprintIdentity

        scores: dict[int, dict] = {}

        # Email matches
        email_values = list(identity.email_contacts.values_list("value", flat=True))
        if email_values:
            shared = (
                ContactEmail.objects.filter(
                    value__in=email_values,
                    identity__isnull=False,
                    identity__status=Identity.ACTIVE,
                )
                .exclude(identity=identity)
                .select_related("identity")
            )

            for match in shared:
                pk = match.identity_id
                if pk not in scores:
                    scores[pk] = {
                        "identity": match.identity,
                        "score": 0.0,
                        "matches": [],
                    }
                scores[pk]["score"] += 0.5
                scores[pk]["matches"].append({"type": "email", "value": match.value})

        # Phone matches
        phone_values = list(identity.phone_contacts.values_list("value", flat=True))
        if phone_values:
            shared = (
                ContactPhone.objects.filter(
                    value__in=phone_values,
                    identity__isnull=False,
                    identity__status=Identity.ACTIVE,
                )
                .exclude(identity=identity)
                .select_related("identity")
            )

            for match in shared:
                pk = match.identity_id
                if pk not in scores:
                    scores[pk] = {
                        "identity": match.identity,
                        "score": 0.0,
                        "matches": [],
                    }
                scores[pk]["score"] += 0.4
                scores[pk]["matches"].append({"type": "phone", "value": match.value})

        # Fingerprint matches
        fp_hashes = list(identity.fingerprints.values_list("hash", flat=True))
        if fp_hashes:
            shared = (
                FingerprintIdentity.objects.filter(
                    hash__in=fp_hashes,
                    identity__isnull=False,
                    identity__status=Identity.ACTIVE,
                )
                .exclude(identity=identity)
                .select_related("identity")
            )

            for match in shared:
                pk = match.identity_id
                if pk not in scores:
                    scores[pk] = {
                        "identity": match.identity,
                        "score": 0.0,
                        "matches": [],
                    }
                scores[pk]["score"] += 0.3
                scores[pk]["matches"].append(
                    {"type": "fingerprint", "value": match.hash[:12]}
                )

        # Sort by score descending
        return sorted(scores.values(), key=lambda x: -x["score"])

    # ── Timeline ─────────────────────────────────────────────────────

    @staticmethod
    def get_identity_timeline(identity: Identity) -> list[dict]:
        """
        Get a formatted timeline of events for an identity.

        Returns:
            List of event dicts with fingerprint details.
        """
        from apps.contacts.fingerprint.models import FingerprintEvent

        fp_ids = list(identity.fingerprints.values_list("id", flat=True))
        events = (
            FingerprintEvent.objects.filter(fingerprint_id__in=fp_ids)
            .select_related("fingerprint")
            .order_by("-timestamp")[:200]
        )

        return [
            {
                "event_type": event.event_type,
                "page_url": event.page_url,
                "timestamp": event.timestamp.isoformat(),
                "session_id": event.session_id,
                "fingerprint_hash": event.fingerprint.hash[:12],
                "device_type": event.fingerprint.device_type,
                "browser": event.fingerprint.browser,
            }
            for event in events
        ]
