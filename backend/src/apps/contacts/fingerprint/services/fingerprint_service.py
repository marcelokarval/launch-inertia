"""
Fingerprint service.

Handles CRUD and analysis for FingerprintIdentity records.
Ported from legacy fingerprint/services/fingerprint_service.py,
adapted to use BaseService[FingerprintIdentity] pattern.
"""

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from core.shared.services.base import BaseService
from apps.contacts.fingerprint.models import FingerprintIdentity

logger = logging.getLogger(__name__)


class FingerprintService(BaseService[FingerprintIdentity]):
    """Service for managing device fingerprint records."""

    model = FingerprintIdentity

    # ── Get or Create ────────────────────────────────────────────────

    @transaction.atomic
    def get_or_create_fingerprint(
        self,
        data: dict,
    ) -> tuple[FingerprintIdentity, bool]:
        """
        Get or create a FingerprintIdentity by hash (visitorId).

        Args:
            data: Dict with at minimum {"hash": "visitor_id_value"}.
                  Optional keys: confidence_score, device_type, browser,
                  os, device_info, browser_info, geo_info, ip_address,
                  user_agent, visitor_found.

        Returns:
            Tuple of (FingerprintIdentity, created: bool)
        """
        hash_value = data.get("hash", "")
        if not hash_value:
            raise ValueError("Fingerprint hash (visitorId) is required")

        fp, created = FingerprintIdentity.objects.get_or_create(
            hash=hash_value,
            defaults={
                "confidence_score": data.get("confidence_score", 0.0),
                "device_type": data.get("device_type", "unknown"),
                "visitor_found": data.get("visitor_found", False),
                "device_info": data.get("device_info", {}),
                "browser_info": data.get("browser_info", {}),
                "geo_info": data.get("geo_info", {}),
                "browser": data.get("browser", ""),
                "os": data.get("os", ""),
                "user_agent": data.get("user_agent", ""),
                "ip_address": data.get("ip_address"),
                "first_seen": timezone.now(),
                "last_seen": timezone.now(),
            },
        )

        if not created:
            fp.update_last_seen()

        logger.info(
            "%s fingerprint: %s",
            "Created" if created else "Found",
            hash_value[:12],
        )
        return fp, created

    # ── Update ───────────────────────────────────────────────────────

    def update_fingerprint_data(
        self,
        fingerprint: FingerprintIdentity,
        new_data: dict,
    ) -> FingerprintIdentity:
        """
        Update fingerprint fields from new payload data.

        Args:
            fingerprint: The fingerprint to update.
            new_data: Dict with updated field values.
        """
        update_fields = ["updated_at"]
        updatable = [
            "device_type",
            "browser",
            "os",
            "user_agent",
            "ip_address",
            "device_info",
            "browser_info",
            "geo_info",
        ]

        for field in updatable:
            if field in new_data:
                setattr(fingerprint, field, new_data[field])
                update_fields.append(field)

        fingerprint.last_seen = timezone.now()
        update_fields.append("last_seen")
        fingerprint.save(update_fields=update_fields)

        logger.info("Updated fingerprint data: %s", fingerprint.hash[:12])
        return fingerprint

    # ── Analysis ─────────────────────────────────────────────────────

    def analyze_fingerprint_patterns(self, identity) -> dict:
        """
        Analyze fingerprint patterns across all fingerprints for an identity.

        Gathers device types, browsers, event types, and stores analysis
        in the identity's metadata.

        Args:
            identity: Identity instance to analyze.

        Returns:
            Dict with analysis results.
        """
        fingerprints = identity.fingerprints.all()

        device_types = set()
        browsers = set()
        event_types = set()

        for fp in fingerprints:
            device_types.add(fp.device_type)
            if fp.browser:
                browsers.add(fp.browser)
            for event in fp.events.all():
                event_types.add(event.event_type)

        analysis = {
            "device_types": list(device_types),
            "browsers": list(browsers),
            "event_types": list(event_types),
            "fingerprint_count": fingerprints.count(),
            "analyzed_at": timezone.now().isoformat(),
        }

        identity.update_metadata({"fingerprint_analysis": analysis})
        logger.info(
            "Analyzed fingerprint patterns for identity: %s", identity.public_id
        )
        return analysis

    # ── Fraud Detection ──────────────────────────────────────────────

    def detect_suspicious_activity(
        self,
        fingerprint: FingerprintIdentity,
    ) -> dict:
        """
        Check for suspicious activity patterns on a fingerprint.

        Looks for:
        - Excessive failed login events
        - Rapid page view patterns
        - Fraud signals from FingerprintJS data

        Returns:
            Dict with is_suspicious bool and details.
        """
        # Check for failed logins in recent events
        recent_events = fingerprint.events.order_by("-timestamp")[:100]
        failed_logins = sum(
            1
            for e in recent_events
            if e.event_type == "form_submit" and e.event_data.get("status") == "failed"
        )

        # Get fraud signals from fingerprint data
        fraud_signals = fingerprint.get_fraud_signals()

        is_suspicious = failed_logins >= 5 or len(fraud_signals) > 0

        result = {
            "is_suspicious": is_suspicious,
            "failed_logins": failed_logins,
            "fraud_signals": fraud_signals,
            "checked_at": timezone.now().isoformat(),
        }

        if is_suspicious:
            logger.warning(
                "Suspicious activity detected for fingerprint: %s (%d failed logins, %d fraud signals)",
                fingerprint.hash[:12],
                failed_logins,
                len(fraud_signals),
            )

        return result
