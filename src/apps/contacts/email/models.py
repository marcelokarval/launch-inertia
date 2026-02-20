"""
Contact email model.

Tracks email addresses captured from registration forms, imports, or API.
Each email is linked to an Identity for cross-channel resolution.
Lifecycle fields track verification status, bounces, DNC, and domain analysis.
"""

from __future__ import annotations

import re

from django.db import models

from core.shared.models.base import BaseModel


class ContactEmail(BaseModel):
    """
    An email address captured as a contact channel.

    Fields from legacy ContactBase (abstract) + ContactEmail (concrete):
    - value: normalized email (lowercase, stripped)
    - original_value: raw input from the user
    - domain: extracted from email
    - is_verified: manual/automatic verification
    - identity: FK to the unified Identity
    - lifecycle_status: state machine for email health
    - is_dnc: do-not-contact flag
    - quality_score: computed quality (0.0-1.0)

    Lifecycle metadata stored in the `metadata` JSONField (from BaseModel):
    - bounce_data: bounce details from ESP
    - verification_code/token: for email verification flow
    - verification_expiry: when verification code/token expires
    """

    PUBLIC_ID_PREFIX = "cem"

    # -- Pyright: FK auto-generated _id attribute --
    identity_id: int | None

    # Lifecycle status choices
    PENDING = "pending"
    ACTIVE = "active"
    INVALID = "invalid"
    BOUNCED_SOFT = "bounced_soft"
    BOUNCED_HARD = "bounced_hard"
    COMPLAINED = "complained"
    UNSUBSCRIBED = "unsubscribed"

    LIFECYCLE_CHOICES = [
        (PENDING, "Pending Verification"),
        (ACTIVE, "Active"),
        (INVALID, "Invalid"),
        (BOUNCED_SOFT, "Soft Bounce"),
        (BOUNCED_HARD, "Hard Bounce"),
        (COMPLAINED, "Complained"),
        (UNSUBSCRIBED, "Unsubscribed"),
    ]

    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="email_contacts",
        verbose_name="Identity",
    )
    value = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Email address",
    )
    original_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Original value",
        help_text="Raw email as entered by the user before normalization",
    )
    domain = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Domain",
        help_text="Extracted domain (e.g., gmail.com)",
    )
    lifecycle_status = models.CharField(
        max_length=20,
        choices=LIFECYCLE_CHOICES,
        default=PENDING,
        db_index=True,
        verbose_name="Lifecycle status",
        help_text="Email health state machine",
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Is verified",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Verified at",
    )
    is_dnc = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Do not contact",
        help_text="Whether this email is on a Do Not Contact list",
    )
    quality_score = models.FloatField(
        default=0.0,
        verbose_name="Quality score",
        help_text="Computed email quality (0.0 - 1.0)",
    )
    value_sha256 = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        verbose_name="SHA-256 hash",
        help_text="Meta-standard SHA-256 of normalized email (for CAPI + cookies)",
    )
    first_seen = models.DateTimeField(
        auto_now_add=True,
        verbose_name="First seen",
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name="Last seen",
    )

    # Searchable fields for SearchManager
    searchable_fields = ["value", "original_value", "domain"]

    class Meta(BaseModel.Meta):
        verbose_name = "Contact Email"
        verbose_name_plural = "Contact Emails"
        indexes = [
            models.Index(fields=["is_verified"]),
            models.Index(fields=["identity"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["first_seen"]),
        ]

    def __str__(self):
        return self.value

    # ── Normalization ────────────────────────────────────────────────

    def normalize(self) -> None:
        """Normalize email: lowercase, strip whitespace, extract domain."""
        if self.value:
            self.value = self.value.lower().strip()
            if "@" in self.value:
                self.domain = self.value.split("@")[1]

    def save(self, *args, **kwargs):
        """Auto-normalize, preserve original value, compute SHA-256 on save."""
        if not self.original_value and self.value:
            self.original_value = self.value
        self.normalize()
        # Auto-compute SHA-256 for Meta CAPI / cookie matching
        if self.value and not self.value_sha256:
            from core.shared.hashing import hash_email

            self.value_sha256 = hash_email(self.value)
        super().save(*args, **kwargs)

    # ── Verification ─────────────────────────────────────────────────

    def verify(self) -> None:
        """Mark this email as verified and set lifecycle to active."""
        from django.utils import timezone

        self.is_verified = True
        self.verified_at = timezone.now()
        self.lifecycle_status = self.ACTIVE
        self.save(
            update_fields=[
                "is_verified",
                "verified_at",
                "lifecycle_status",
                "updated_at",
            ]
        )

    def unverify(self) -> None:
        """Remove verification status and reset lifecycle to pending."""
        self.is_verified = False
        self.verified_at = None
        self.lifecycle_status = self.PENDING
        self.save(
            update_fields=[
                "is_verified",
                "verified_at",
                "lifecycle_status",
                "updated_at",
            ]
        )

    def mark_bounced(self, hard: bool = False) -> None:
        """Mark this email as bounced."""
        self.lifecycle_status = self.BOUNCED_HARD if hard else self.BOUNCED_SOFT
        self.is_verified = False
        self.save(update_fields=["lifecycle_status", "is_verified", "updated_at"])

    def mark_complained(self) -> None:
        """Mark this email as complained (spam report)."""
        self.lifecycle_status = self.COMPLAINED
        self.is_dnc = True
        self.save(update_fields=["lifecycle_status", "is_dnc", "updated_at"])

    def mark_unsubscribed(self) -> None:
        """Mark this email as unsubscribed."""
        self.lifecycle_status = self.UNSUBSCRIBED
        self.is_dnc = True
        self.save(update_fields=["lifecycle_status", "is_dnc", "updated_at"])

    def mark_invalid(self) -> None:
        """Mark this email as invalid."""
        self.lifecycle_status = self.INVALID
        self.is_verified = False
        self.save(update_fields=["lifecycle_status", "is_verified", "updated_at"])

    @property
    def is_deliverable(self) -> bool:
        """Whether email is likely to receive messages."""
        return self.lifecycle_status in (self.PENDING, self.ACTIVE) and not self.is_dnc

    # ── Validation ───────────────────────────────────────────────────

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Basic email format validation."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "value": self.value,
                "original_value": self.original_value,
                "domain": self.domain,
                "lifecycle_status": self.lifecycle_status,
                "is_verified": self.is_verified,
                "verified_at": self.verified_at.isoformat()
                if self.verified_at
                else None,
                "is_dnc": self.is_dnc,
                "is_deliverable": self.is_deliverable,
                "quality_score": self.quality_score,
                "first_seen": self.first_seen.isoformat() if self.first_seen else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "identity_id": self.identity.public_id if self.identity else None,
            }
        )
        return data
