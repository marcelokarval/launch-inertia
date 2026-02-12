"""
LifecycleService — manages the lifecycle_global JSONB cache on Identity.

Responsible for:
- Initializing the lifecycle_global schema with default/empty values
- Recalculating sections from real data (channels, timeline, scores)
- Providing update methods for future phases (launches, financial, behavior, tags)
- Expand-on-demand data loading for detail views

Schema version: 1 (as documented in CONTACTS_ANALYSIS.md Q40)

The lifecycle_global is a CACHE — it aggregates data from:
- ContactEmail, ContactPhone, FingerprintIdentity (channels)
- Identity timestamps (timeline)
- ConfidenceEngine (scores)
- LaunchParticipant (launches, financial, behavior) — Phase 4
- Tags (tags) — from Identity.tags M2M

Update strategy:
- Signals/tasks trigger recalculation when events happen
- Each section can be updated independently (partial update)
- _version field enables progressive migration without breaking old data
- _updated_at tracks cache freshness
"""

import logging
from datetime import datetime
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

# Current schema version
LIFECYCLE_SCHEMA_VERSION = 1


class LifecycleService:
    """
    Manages the lifecycle_global JSONB cache on Identity.

    All methods are classmethods — no instance state needed.
    """

    # ── Schema ────────────────────────────────────────────────────────

    @classmethod
    def get_empty_schema(cls) -> dict:
        """
        Return a fresh lifecycle_global schema with zero/empty values.

        This is the canonical schema from CONTACTS_ANALYSIS.md Q40.
        Used when initializing a new Identity or resetting the cache.
        """
        return {
            "_version": LIFECYCLE_SCHEMA_VERSION,
            "_updated_at": None,
            "timeline": {
                "first_seen": None,
                "last_seen": None,
                "first_purchase": None,
                "last_purchase": None,
                "days_since_first_seen": None,
                "days_since_last_seen": None,
                "days_since_last_purchase": None,
            },
            "launches": {
                "total_participated": 0,
                "total_as_visitor": 0,
                "total_as_lead": 0,
                "total_as_buyer": 0,
                "total_as_student": 0,
                "total_refunded": 0,
                "total_churned": 0,
                "active": [],
                "history": [],
                "is_recurrent": False,
                "recurrence_rate": 0.0,
            },
            "financial": {
                "total_spent": 0.0,
                "total_refunded": 0.0,
                "net_revenue": 0.0,
                "average_ticket": 0.0,
                "ltv_estimated": 0.0,
                "currency": "BRL",
                "products_purchased": [],
                "has_active_subscription": False,
                "is_delinquent": False,
            },
            "behavior": {
                "pattern": None,
                "avg_days_to_purchase": None,
                "total_page_views": 0,
                "total_form_submissions": 0,
                "total_entries": 0,
                "preferred_device": None,
                "preferred_time": None,
                "engagement_score": 0.0,
                "risk_score": 0.0,
            },
            "channels": {
                "emails": {
                    "total": 0,
                    "verified": 0,
                    "primary": None,
                },
                "phones": {
                    "total": 0,
                    "verified": 0,
                    "whatsapp": 0,
                    "primary": None,
                },
                "fingerprints": {
                    "total": 0,
                    "devices": [],
                },
            },
            "tags": {
                "accumulated": [],
                "current_active": [],
                "manual": [],
            },
            "scores": {
                "confidence": 0.0,
                "engagement": 0.0,
                "risk": 0.0,
                "ltv_tier": None,
            },
        }

    # ── Full Recalculation ────────────────────────────────────────────

    @classmethod
    @transaction.atomic
    def recalculate(cls, identity) -> dict:
        """
        Full recalculation of lifecycle_global from source data.

        Rebuilds all sections that can be computed from current data:
        - channels (from ContactEmail, ContactPhone, FingerprintIdentity)
        - timeline (from Identity timestamps)
        - scores (from ConfidenceEngine + channels)
        - tags (from Identity.tags M2M)
        - behavior (partial — page views/form submissions from FingerprintEvent)

        Sections that require LaunchParticipant (Phase 4) are preserved
        if they already have data, otherwise initialized to empty.

        Args:
            identity: Identity instance to recalculate.

        Returns:
            The updated lifecycle_global dict.
        """
        # Start from existing data (preserve launch/financial data from Phase 4+)
        # or empty schema if nothing exists yet
        current = identity.lifecycle_global or {}
        if not current or current.get("_version") is None:
            lifecycle = cls.get_empty_schema()
        else:
            lifecycle = cls._ensure_schema_fields(current)

        # Recalculate sections from real data
        cls._update_channels(lifecycle, identity)
        cls._update_timeline(lifecycle, identity)
        cls._update_scores(lifecycle, identity)
        cls._update_tags(lifecycle, identity)
        cls._update_behavior_from_fingerprints(lifecycle, identity)

        # Stamp metadata
        lifecycle["_version"] = LIFECYCLE_SCHEMA_VERSION
        lifecycle["_updated_at"] = timezone.now().isoformat()

        # Save
        identity.lifecycle_global = lifecycle
        identity.save(update_fields=["lifecycle_global", "updated_at"])

        logger.info(
            "Recalculated lifecycle_global for identity %s",
            identity.public_id,
        )
        return lifecycle

    # ── Section Updaters ──────────────────────────────────────────────

    @classmethod
    def _update_channels(cls, lifecycle: dict, identity) -> None:
        """Update channels section from ContactEmail, ContactPhone, FingerprintIdentity."""
        emails = identity.email_contacts.filter(is_deleted=False)
        phones = identity.phone_contacts.filter(is_deleted=False)
        fingerprints = identity.fingerprints.filter(is_deleted=False)

        # Primary email: first verified, or first by created_at
        primary_email = (
            emails.filter(is_verified=True).order_by("created_at").first()
            or emails.order_by("created_at").first()
        )

        # Primary phone: first verified, or first by created_at
        primary_phone = (
            phones.filter(is_verified=True).order_by("created_at").first()
            or phones.order_by("created_at").first()
        )

        # Device types from fingerprints (stored in metadata)
        devices = set()
        for fp in fingerprints:
            device_type = None
            if fp.metadata and isinstance(fp.metadata, dict):
                device_type = fp.metadata.get("device_type")
            if device_type:
                devices.add(device_type)

        lifecycle["channels"] = {
            "emails": {
                "total": emails.count(),
                "verified": emails.filter(is_verified=True).count(),
                "primary": primary_email.value if primary_email else None,
            },
            "phones": {
                "total": phones.count(),
                "verified": phones.filter(is_verified=True).count(),
                "whatsapp": phones.filter(is_whatsapp=True).count(),
                "primary": primary_phone.value if primary_phone else None,
            },
            "fingerprints": {
                "total": fingerprints.count(),
                "devices": sorted(devices),
            },
        }

    @classmethod
    def _update_timeline(cls, lifecycle: dict, identity) -> None:
        """Update timeline section from Identity timestamps."""
        now = timezone.now()

        first_seen = identity.created_at
        last_seen = identity.last_seen or identity.updated_at

        # Get first_purchase and last_purchase from financial (preserved from Phase 4)
        # For now these stay as-is from existing data
        existing_timeline = lifecycle.get("timeline", {})
        first_purchase = existing_timeline.get("first_purchase")
        last_purchase = existing_timeline.get("last_purchase")

        days_since_first_seen = None
        if first_seen:
            days_since_first_seen = (now - first_seen).days

        days_since_last_seen = None
        if last_seen:
            days_since_last_seen = (now - last_seen).days

        days_since_last_purchase = None
        if last_purchase:
            try:
                lp_dt = datetime.fromisoformat(last_purchase)
                if lp_dt.tzinfo is None:
                    from django.utils.timezone import make_aware

                    lp_dt = make_aware(lp_dt)
                days_since_last_purchase = (now - lp_dt).days
            except (ValueError, TypeError):
                pass

        lifecycle["timeline"] = {
            "first_seen": first_seen.isoformat() if first_seen else None,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "first_purchase": first_purchase,
            "last_purchase": last_purchase,
            "days_since_first_seen": days_since_first_seen,
            "days_since_last_seen": days_since_last_seen,
            "days_since_last_purchase": days_since_last_purchase,
        }

    @classmethod
    def _update_scores(cls, lifecycle: dict, identity) -> None:
        """Update scores section from ConfidenceEngine + behavior data."""
        lifecycle["scores"] = {
            "confidence": identity.confidence_score,
            "engagement": lifecycle.get("behavior", {}).get("engagement_score", 0.0),
            "risk": lifecycle.get("behavior", {}).get("risk_score", 0.0),
            "ltv_tier": cls._calculate_ltv_tier(lifecycle),
        }

    @classmethod
    def _update_tags(cls, lifecycle: dict, identity) -> None:
        """Update tags section from Identity.tags M2M."""
        all_tags = identity.tags.filter(is_deleted=False)

        # All tag names
        accumulated = [t.name for t in all_tags]

        # Manual tags: tags that don't match launch patterns (no uppercase + numbers)
        import re

        launch_pattern = re.compile(r"^[A-Z]+\d+")
        manual = [t.name for t in all_tags if not launch_pattern.match(t.name)]

        # Active tags: for now, same as accumulated (Phase 4 will filter by active launches)
        current_active = accumulated

        lifecycle["tags"] = {
            "accumulated": accumulated,
            "current_active": current_active,
            "manual": manual,
        }

    @classmethod
    def _update_behavior_from_fingerprints(cls, lifecycle: dict, identity) -> None:
        """Update behavior section from FingerprintEvent data (partial)."""
        from apps.contacts.fingerprint.models import FingerprintEvent

        fingerprint_ids = identity.fingerprints.values_list("id", flat=True)

        if not fingerprint_ids:
            # Preserve existing behavior data but ensure structure
            if "behavior" not in lifecycle:
                lifecycle["behavior"] = cls.get_empty_schema()["behavior"]
            return

        events = FingerprintEvent.objects.filter(fingerprint_id__in=fingerprint_ids)

        total_page_views = events.filter(event_type="page_view").count()
        total_form_submissions = events.filter(event_type="form_submit").count()

        # Detect preferred device from event metadata
        device_counts: dict[str, int] = {}
        for event in events.only("metadata"):
            if event.metadata and isinstance(event.metadata, dict):
                device = event.metadata.get("device_type")
                if device:
                    device_counts[device] = device_counts.get(device, 0) + 1

        preferred_device = None
        if device_counts:
            preferred_device = max(device_counts, key=device_counts.get)

        # Detect preferred time from event timestamps
        hour_counts: dict[str, int] = {}
        for event in events.only("timestamp"):
            if event.timestamp:
                hour = event.timestamp.hour
                if 6 <= hour < 12:
                    period = "morning"
                elif 12 <= hour < 18:
                    period = "afternoon"
                elif 18 <= hour < 22:
                    period = "evening"
                else:
                    period = "night"
                hour_counts[period] = hour_counts.get(period, 0) + 1

        preferred_time = None
        if hour_counts:
            preferred_time = max(hour_counts, key=hour_counts.get)

        # Preserve launch-dependent fields from existing data
        existing_behavior = lifecycle.get("behavior", {})

        lifecycle["behavior"] = {
            "pattern": existing_behavior.get("pattern"),
            "avg_days_to_purchase": existing_behavior.get("avg_days_to_purchase"),
            "total_page_views": total_page_views,
            "total_form_submissions": total_form_submissions,
            "total_entries": existing_behavior.get("total_entries", 0),
            "preferred_device": preferred_device,
            "preferred_time": preferred_time,
            "engagement_score": existing_behavior.get("engagement_score", 0.0),
            "risk_score": existing_behavior.get("risk_score", 0.0),
        }

    # ── Partial Update Methods (for Phase 4+) ────────────────────────

    @classmethod
    @transaction.atomic
    def update_launches_section(cls, identity, launches_data: dict) -> dict:
        """
        Update only the launches section of lifecycle_global.

        Called by ParticipantService when a LaunchParticipant is created/updated.

        Args:
            identity: Identity instance.
            launches_data: Dict matching the launches schema section.

        Returns:
            Updated lifecycle_global.
        """
        lifecycle = cls._get_or_init(identity)
        lifecycle["launches"].update(launches_data)
        lifecycle["_updated_at"] = timezone.now().isoformat()

        identity.lifecycle_global = lifecycle
        identity.save(update_fields=["lifecycle_global", "updated_at"])
        return lifecycle

    @classmethod
    @transaction.atomic
    def update_financial_section(cls, identity, financial_data: dict) -> dict:
        """
        Update only the financial section of lifecycle_global.

        Called by Stripe webhook handlers when a purchase/refund occurs.

        Args:
            identity: Identity instance.
            financial_data: Dict matching the financial schema section.

        Returns:
            Updated lifecycle_global.
        """
        lifecycle = cls._get_or_init(identity)
        lifecycle["financial"].update(financial_data)

        # Update timeline purchase dates if provided
        if "last_purchase" in financial_data:
            lifecycle["timeline"]["last_purchase"] = financial_data["last_purchase"]
        if "first_purchase" in financial_data:
            lifecycle["timeline"]["first_purchase"] = financial_data["first_purchase"]

        # Recalculate LTV tier
        lifecycle["scores"]["ltv_tier"] = cls._calculate_ltv_tier(lifecycle)

        lifecycle["_updated_at"] = timezone.now().isoformat()

        identity.lifecycle_global = lifecycle
        identity.save(update_fields=["lifecycle_global", "updated_at"])
        return lifecycle

    @classmethod
    @transaction.atomic
    def update_behavior_section(cls, identity, behavior_data: dict) -> dict:
        """
        Update only the behavior section of lifecycle_global.

        Called when behavior analysis is recalculated (e.g., after a launch closes).

        Args:
            identity: Identity instance.
            behavior_data: Dict matching the behavior schema section.

        Returns:
            Updated lifecycle_global.
        """
        lifecycle = cls._get_or_init(identity)
        lifecycle["behavior"].update(behavior_data)

        # Sync scores
        lifecycle["scores"]["engagement"] = behavior_data.get(
            "engagement_score", lifecycle["scores"].get("engagement", 0.0)
        )
        lifecycle["scores"]["risk"] = behavior_data.get(
            "risk_score", lifecycle["scores"].get("risk", 0.0)
        )

        lifecycle["_updated_at"] = timezone.now().isoformat()

        identity.lifecycle_global = lifecycle
        identity.save(update_fields=["lifecycle_global", "updated_at"])
        return lifecycle

    @classmethod
    @transaction.atomic
    def record_entry(cls, identity) -> dict:
        """
        Record a new entry (form submission / registration).

        Increments total_entries and total_form_submissions in behavior.

        Args:
            identity: Identity instance.

        Returns:
            Updated lifecycle_global.
        """
        lifecycle = cls._get_or_init(identity)

        behavior = lifecycle.get("behavior", {})
        behavior["total_entries"] = behavior.get("total_entries", 0) + 1
        behavior["total_form_submissions"] = (
            behavior.get("total_form_submissions", 0) + 1
        )
        lifecycle["behavior"] = behavior

        lifecycle["_updated_at"] = timezone.now().isoformat()

        identity.lifecycle_global = lifecycle
        identity.save(update_fields=["lifecycle_global", "updated_at"])
        return lifecycle

    # ── Expand-On-Demand ──────────────────────────────────────────────

    @classmethod
    def get_expanded_data(cls, identity) -> dict:
        """
        Load full expanded data for an Identity's detail view.

        This is the "expand on demand" endpoint data — called when
        the operator clicks "Ver detalhes" on an Identity card.

        Currently returns channel details. Phase 4 will add
        LaunchParticipant data per launch.

        Args:
            identity: Identity instance.

        Returns:
            Dict with expanded sections ready for frontend rendering.
        """
        # Channel details
        emails = [
            {
                "id": e.public_id,
                "value": e.value,
                "is_verified": e.is_verified,
                "lifecycle_status": e.lifecycle_status,
                "is_dnc": e.is_dnc,
                "quality_score": e.quality_score,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
            }
            for e in identity.email_contacts.filter(is_deleted=False).order_by(
                "created_at"
            )
        ]

        phones = [
            {
                "id": p.public_id,
                "value": p.value,
                "display_value": p.format_for_display(),
                "is_verified": p.is_verified,
                "phone_type": p.phone_type,
                "is_whatsapp": p.is_whatsapp,
                "is_dnc": p.is_dnc,
                "first_seen": p.first_seen.isoformat() if p.first_seen else None,
            }
            for p in identity.phone_contacts.filter(is_deleted=False).order_by(
                "created_at"
            )
        ]

        fingerprints = [
            {
                "id": f.public_id,
                "visitor_id": f.visitor_id if hasattr(f, "visitor_id") else None,
                "device_type": f.metadata.get("device_type") if f.metadata else None,
                "first_seen": f.created_at.isoformat() if f.created_at else None,
                "last_seen": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in identity.fingerprints.filter(is_deleted=False).order_by(
                "created_at"
            )
        ]

        # Attribution history
        attributions = [
            {
                "id": a.public_id,
                "utm_source": a.utm_source,
                "utm_medium": a.utm_medium,
                "utm_campaign": a.utm_campaign,
                "touchpoint_type": a.touchpoint_type,
                "landing_page": a.landing_page,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in identity.attributions.all()[:50]
        ]

        # Lifecycle cache (current state)
        lifecycle = identity.lifecycle_global or cls.get_empty_schema()

        # Placeholder for Phase 4 — will return per-launch data
        launches = []
        # When LaunchParticipant exists (Phase 4):
        # launches = [
        #     {
        #         "launch": lp.launch.tag,
        #         "launch_name": lp.launch.name,
        #         "status": lp.status,
        #         "enrolled_at": lp.created_at.isoformat(),
        #         "entries": lp.entry_count,
        #         "products": [...],
        #         "tags": [...],
        #     }
        #     for lp in identity.launch_participants.all()
        # ]

        return {
            "emails": emails,
            "phones": phones,
            "fingerprints": fingerprints,
            "attributions": attributions,
            "lifecycle": lifecycle,
            "launches": launches,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    @classmethod
    def _get_or_init(cls, identity) -> dict:
        """Get existing lifecycle_global or initialize with empty schema."""
        current = identity.lifecycle_global
        if (
            not current
            or not isinstance(current, dict)
            or current.get("_version") is None
        ):
            return cls.get_empty_schema()
        return cls._ensure_schema_fields(current)

    @classmethod
    def _ensure_schema_fields(cls, data: dict) -> dict:
        """
        Ensure all schema sections exist, filling missing sections with defaults.

        This handles forward-compatibility: if a section is added in a later
        schema version, old records get it filled with defaults on next recalculation.
        """
        empty = cls.get_empty_schema()
        for section_key, section_default in empty.items():
            if section_key.startswith("_"):
                continue
            if section_key not in data:
                data[section_key] = section_default
            elif isinstance(section_default, dict) and isinstance(
                data[section_key], dict
            ):
                # Fill missing sub-keys
                for sub_key, sub_default in section_default.items():
                    if sub_key not in data[section_key]:
                        data[section_key][sub_key] = sub_default
        return data

    @classmethod
    def _calculate_ltv_tier(cls, lifecycle: dict) -> Optional[str]:
        """
        Calculate LTV tier based on financial data.

        Tiers:
        - "high": total_spent >= 5000 BRL
        - "medium": total_spent >= 1000 BRL
        - "low": total_spent > 0
        - None: no purchases
        """
        total_spent = lifecycle.get("financial", {}).get("total_spent", 0.0)
        if total_spent >= 5000:
            return "high"
        elif total_spent >= 1000:
            return "medium"
        elif total_spent > 0:
            return "low"
        return None
