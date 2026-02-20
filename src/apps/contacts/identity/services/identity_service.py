"""
Identity CRUD service.

Handles basic CRUD, history tracking, and confidence scoring
for Identity records.

Ported from legacy identity/services/identity_service.py.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from core.shared.services.base import BaseService
from apps.contacts.identity.models import Identity, IdentityHistory

logger = logging.getLogger(__name__)


class IdentityService(BaseService[Identity]):
    """Service for managing identity records."""

    model = Identity

    # ── Create ───────────────────────────────────────────────────────

    @transaction.atomic
    def create_identity(
        self,
        source: str | None = None,
    ) -> Identity:
        """
        Create a new active Identity.

        Args:
            source: Where the identity was first observed (e.g., "form", "api").

        Returns:
            New Identity instance.
        """
        identity = Identity.objects.create(
            status=Identity.ACTIVE,
            first_seen_source=source or "unknown",
            last_seen=timezone.now(),
        )

        # Record creation in history
        IdentityHistory.objects.create(
            identity=identity,
            operation_type=IdentityHistory.UPDATE,
            details={"action": "created", "source": source or "unknown"},
        )

        logger.info("Created identity: %s (source: %s)", identity.public_id, source)
        return identity

    # ── History ──────────────────────────────────────────────────────

    @staticmethod
    def update_identity_history(
        identity: Identity,
        operation_type: str,
        details: dict | None = None,
    ) -> IdentityHistory:
        """Create an audit history record for an identity operation."""
        return IdentityHistory.objects.create(
            identity=identity,
            operation_type=operation_type,
            details=details or {},
        )

    # ── Confidence Scoring ───────────────────────────────────────────

    @staticmethod
    def calculate_confidence_score(identity: Identity) -> float:
        """
        Calculate the confidence score for an identity.

        Delegates to the unified ConfidenceEngine which considers:
        - FingerprintJS confidence averages
        - Verified/unverified email/phone bonuses
        - Cross-device bonuses
        - Fraud penalties (incognito, VPN)
        - Contact quality penalties (bounced, DNC)

        Returns the computed score (0.0 - 1.0), saved to the identity.
        """
        from apps.contacts.identity.services.confidence_engine import ConfidenceEngine

        return ConfidenceEngine.calculate(identity)

    # ── Relationship Queries ─────────────────────────────────────────

    @staticmethod
    def get_identity_contacts(identity: Identity) -> dict:
        """Get all contacts for an identity grouped by type."""
        return {
            "emails": list(identity.email_contacts.all()),
            "phones": list(identity.phone_contacts.all()),
        }

    @staticmethod
    def get_identity_fingerprints(identity: Identity) -> list:
        """Get all fingerprints for an identity."""
        return list(identity.fingerprints.all())

    @staticmethod
    def get_identity_timeline(identity: Identity):
        """Get all events across all fingerprints for this identity."""
        return identity.get_timeline()

    # ── Status Management ────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_identity_status(
        identity: Identity,
        new_status: str,
    ) -> Identity:
        """Update identity status with history record."""
        old_status = identity.status
        identity.status = new_status
        identity.save(update_fields=["status", "updated_at"])

        IdentityHistory.objects.create(
            identity=identity,
            operation_type=IdentityHistory.STATUS_CHANGE,
            details={
                "old_status": old_status,
                "new_status": new_status,
            },
        )

        logger.info(
            "Identity %s status: %s -> %s",
            identity.public_id,
            old_status,
            new_status,
        )
        return identity

    @staticmethod
    def update_identity_last_seen(identity: Identity) -> None:
        """Update last_seen timestamp."""
        identity.update_last_seen()
