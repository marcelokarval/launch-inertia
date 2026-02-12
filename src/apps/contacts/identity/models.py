"""
Identity resolution models.

Identity represents a unified person across multiple contact channels
(emails, phones) and device fingerprints. The resolution algorithm links
contacts and fingerprints to create a single identity, with confidence
scoring and merge capabilities.
"""

from django.db import models
from django.utils import timezone

from core.shared.models.base import BaseModel


class Identity(BaseModel):
    """
    Unified identity representing a single person across channels.

    An identity aggregates:
    - Multiple ContactEmail records
    - Multiple ContactPhone records
    - Multiple FingerprintIdentity records

    Identities can be merged when the resolution algorithm determines
    two identities represent the same person (confidence >= 0.9).
    """

    PUBLIC_ID_PREFIX = "idt"

    # Status constants
    ACTIVE = "active"
    MERGED = "merged"
    INACTIVE = "inactive"
    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (MERGED, "Merged"),
        (INACTIVE, "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ACTIVE,
        db_index=True,
        verbose_name="Status",
    )
    merged_into = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="merged_identities",
        verbose_name="Merged into",
        help_text="The identity this was merged into",
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last seen",
    )
    first_seen_source = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="First seen source",
        help_text="Source where this identity was first observed (e.g., form, API)",
    )
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name="Confidence score",
        help_text="Overall confidence score (0.0 - 1.0)",
    )

    # ── New fields (Phase 0: Identity becomes primary entity) ────────
    display_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Display name",
        help_text="Name for display (from capture form or inferred from email)",
    )
    operator_notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Operator notes",
        help_text="Free-form notes by the operator about this identity",
    )
    tags = models.ManyToManyField(
        "contacts.Tag",
        blank=True,
        related_name="identities",
        verbose_name="Tags",
        help_text="Manual operator tags + automatic launch tags",
    )
    lifecycle_global = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Global lifecycle",
        help_text="JSONB cache of cross-launch lifecycle data (updated by signals/tasks)",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Identity"
        verbose_name_plural = "Identities"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["merged_into"]),
            models.Index(fields=["last_seen"]),
            models.Index(fields=["confidence_score"]),
        ]

    def __str__(self):
        return f"Identity({self.public_id}, {self.status})"

    # ── Relationships ────────────────────────────────────────────────

    def get_merged_identities(self):
        """Get all identities that were merged into this one."""
        return Identity.objects.filter(merged_into=self, status=self.MERGED)

    def get_all_emails(self):
        """Get all ContactEmail records linked to this identity."""
        return self.email_contacts.all()

    def get_all_phones(self):
        """Get all ContactPhone records linked to this identity."""
        return self.phone_contacts.all()

    def get_all_fingerprints(self):
        """Get all FingerprintIdentity records linked to this identity."""
        return self.fingerprints.all()

    def get_all_contacts(self) -> dict:
        """Get all contacts grouped by type."""
        return {
            "emails": list(self.get_all_emails()),
            "phones": list(self.get_all_phones()),
        }

    # ── Timeline ─────────────────────────────────────────────────────

    def get_timeline(self):
        """
        Get all events across all fingerprints for this identity,
        ordered by most recent first.
        """
        from apps.contacts.fingerprint.models import FingerprintEvent

        fingerprint_ids = self.fingerprints.values_list("id", flat=True)
        return FingerprintEvent.objects.filter(
            fingerprint_id__in=fingerprint_ids
        ).order_by("-timestamp")

    # ── Status Management ────────────────────────────────────────────

    def mark_as_merged(self, target: "Identity") -> None:
        """Mark this identity as merged into another."""
        self.status = self.MERGED
        self.merged_into = target
        self.save(update_fields=["status", "merged_into", "updated_at"])

    def mark_as_inactive(self) -> None:
        """Mark this identity as inactive."""
        self.status = self.INACTIVE
        self.save(update_fields=["status", "updated_at"])

    def update_last_seen(self) -> None:
        """Update last_seen to now."""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen", "updated_at"])

    # ── Serialization ────────────────────────────────────────────────

    def to_list_dict(self) -> dict:
        """Lightweight serialization for list views (Index page)."""
        primary_email = self.email_contacts.first()
        primary_phone = self.phone_contacts.first()
        return {
            "id": self.public_id,
            "display_name": self.display_name,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "primary_email": primary_email.value if primary_email else None,
            "primary_phone": primary_phone.value if primary_phone else None,
            "email_count": self.email_contacts.count(),
            "phone_count": self.phone_contacts.count(),
            "fingerprint_count": self.fingerprints.count(),
            "tags": [
                {"id": t.public_id, "name": t.name, "color": t.color}
                for t in self.tags.all()
            ],
            "lifecycle_global": self.lifecycle_global,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict(self, include_contacts: bool = False, **kwargs) -> dict:
        """Serialize identity for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "status": self.status,
                "merged_into_id": self.merged_into.public_id
                if self.merged_into
                else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "first_seen_source": self.first_seen_source,
                "confidence_score": self.confidence_score,
                "email_count": self.email_contacts.count(),
                "phone_count": self.phone_contacts.count(),
                "fingerprint_count": self.fingerprints.count(),
            }
        )
        if include_contacts:
            data["emails"] = [e.to_dict() for e in self.get_all_emails()]
            data["phones"] = [p.to_dict() for p in self.get_all_phones()]
            data["fingerprints"] = [f.to_dict() for f in self.get_all_fingerprints()]
        return data


class Attribution(BaseModel):
    """
    Marketing attribution data linked to an Identity.

    Captures UTM parameters, referrer, and landing page for each
    touchpoint. An identity can have multiple attributions (one per
    form submission or event that includes attribution data).

    This is essential for launch marketing where you need to know
    which campaign/source drove each registration.
    """

    PUBLIC_ID_PREFIX = "atr"

    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="attributions",
        verbose_name="Identity",
    )
    # UTM parameters
    utm_source = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="UTM Source",
        help_text="e.g., google, facebook, youtube",
    )
    utm_medium = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="UTM Medium",
        help_text="e.g., cpc, email, social",
    )
    utm_campaign = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name="UTM Campaign",
        help_text="e.g., WH0126_launch, MDL0125_webinar",
    )
    utm_content = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="UTM Content",
        help_text="e.g., banner_top, cta_bottom",
    )
    utm_term = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="UTM Term",
        help_text="Keyword for paid search",
    )
    # Referrer and landing page
    referrer = models.URLField(
        max_length=2048,
        blank=True,
        verbose_name="Referrer URL",
    )
    landing_page = models.URLField(
        max_length=2048,
        blank=True,
        verbose_name="Landing Page URL",
    )
    # Touchpoint context
    touchpoint_type = models.CharField(
        max_length=50,
        blank=True,
        default="form",
        verbose_name="Touchpoint type",
        help_text="e.g., form, api, import, webhook",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Attribution"
        verbose_name_plural = "Attributions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["identity", "-created_at"]),
            models.Index(fields=["utm_source"]),
            models.Index(fields=["utm_campaign"]),
        ]

    def __str__(self):
        parts = []
        if self.utm_source:
            parts.append(f"src={self.utm_source}")
        if self.utm_medium:
            parts.append(f"med={self.utm_medium}")
        if self.utm_campaign:
            parts.append(f"cmp={self.utm_campaign}")
        return " ".join(parts) or f"Attribution({self.public_id})"

    def to_dict(self, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "identity_id": self.identity.public_id,
                "utm_source": self.utm_source,
                "utm_medium": self.utm_medium,
                "utm_campaign": self.utm_campaign,
                "utm_content": self.utm_content,
                "utm_term": self.utm_term,
                "referrer": self.referrer,
                "landing_page": self.landing_page,
                "touchpoint_type": self.touchpoint_type,
            }
        )
        return data

    @property
    def has_utm(self) -> bool:
        """Whether any UTM parameters are present."""
        return bool(self.utm_source or self.utm_medium or self.utm_campaign)


class IdentityHistory(BaseModel):
    """
    Audit log for identity operations (merges, status changes, etc.).

    Every significant operation on an identity creates a history record
    for traceability and debugging.
    """

    PUBLIC_ID_PREFIX = "idh"

    # Operation types
    MERGE = "MERGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    CONTACT_ADDED = "CONTACT_ADDED"
    CONTACT_REMOVED = "CONTACT_REMOVED"
    FINGERPRINT_LINKED = "FINGERPRINT_LINKED"
    CONFIDENCE_UPDATE = "CONFIDENCE_UPDATE"
    UPDATE = "UPDATE"

    OPERATION_CHOICES = [
        (MERGE, "Identity Merge"),
        (STATUS_CHANGE, "Status Change"),
        (CONTACT_ADDED, "Contact Added"),
        (CONTACT_REMOVED, "Contact Removed"),
        (FINGERPRINT_LINKED, "Fingerprint Linked"),
        (CONFIDENCE_UPDATE, "Confidence Score Update"),
        (UPDATE, "General Update"),
    ]

    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Identity",
    )
    operation_type = models.CharField(
        max_length=50,
        choices=OPERATION_CHOICES,
        verbose_name="Operation type",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Timestamp",
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Details",
        help_text="Additional context about the operation (JSON)",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Identity History"
        verbose_name_plural = "Identity Histories"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["identity", "-timestamp"]),
            models.Index(fields=["operation_type"]),
        ]

    def __str__(self):
        return f"{self.operation_type} on {self.identity.public_id} at {self.timestamp}"
