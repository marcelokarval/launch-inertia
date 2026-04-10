"""
Fingerprint tracking models.

Tracks device fingerprints from FingerprintJS Pro for identity resolution.
Three models:
- FingerprintIdentity: the primary device fingerprint (visitorId)
- FingerprintEvent: page views, form submissions, and other tracked events
- FingerprintContact: polymorphic M2M linking fingerprints to ContactEmail/ContactPhone
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from core.shared.models.base import BaseModel

if TYPE_CHECKING:
    from django.db.models import Manager


class FingerprintIdentity(BaseModel):
    """
    A device fingerprint from FingerprintJS Pro.

    The `hash` field stores the visitorId from FingerprintJS Pro.
    Confidence score comes from FingerprintJS + local enrichment.
    Device/browser/geo info is parsed from the FingerprintJS payload.

    This is the primary fingerprint model (replaces legacy FingerprintBase).
    """

    PUBLIC_ID_PREFIX = "fpi"
    HASH_LENGTH = 64

    # -- Pyright: FK _id + reverse relation managers --
    identity_id: int | None
    if TYPE_CHECKING:
        events: Manager[FingerprintEvent]
        contacts: Manager[FingerprintContact]

    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fingerprints",
        verbose_name="Identity",
    )
    hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="Visitor ID hash",
        help_text="visitorId from FingerprintJS Pro",
    )
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name="Confidence score",
        help_text="FingerprintJS confidence (0.0 - 1.0)",
    )
    device_type = models.CharField(
        max_length=50,
        default="unknown",
        verbose_name="Device type",
        help_text="mobile, tablet, desktop, unknown",
    )
    visitor_found = models.BooleanField(
        default=False,
        verbose_name="Visitor found",
        help_text="Whether FingerprintJS found a returning visitor",
    )

    # Structured info from FingerprintJS payload
    device_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Device info",
        help_text="Parsed device details (model, brand, screen, etc.)",
    )
    browser_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Browser info",
        help_text="Browser name, version, engine, capabilities",
    )
    geo_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Geolocation info",
        help_text="Country, city, timezone, coordinates, accuracy",
    )

    # Convenience fields extracted from JSON
    browser = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Browser",
    )
    os = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Operating system",
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User agent",
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP address",
    )

    # Timing
    first_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="First seen",
    )
    last_seen = models.DateTimeField(
        default=timezone.now,
        verbose_name="Last seen",
    )
    is_master = models.BooleanField(
        default=False,
        verbose_name="Is master fingerprint",
        help_text="Primary fingerprint for the linked identity",
    )

    # Searchable fields
    searchable_fields = ["hash", "browser", "os", "ip_address"]

    class Meta(BaseModel.Meta):
        verbose_name = "Fingerprint Identity"
        verbose_name_plural = "Fingerprint Identities"
        indexes = [
            models.Index(fields=["device_type", "browser"]),
            models.Index(fields=["last_seen"]),
            models.Index(fields=["identity"]),
            models.Index(fields=["confidence_score"]),
        ]

    def __str__(self):
        return f"FP({self.hash[:12]}..., {self.device_type})"

    # ── Updates ──────────────────────────────────────────────────────

    def update_last_seen(self) -> None:
        """Update last_seen to now."""
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen", "updated_at"])

    def update_from_payload(self, payload_data: dict) -> None:
        """
        Update fingerprint fields from a FingerprintJS Pro payload.

        Expected payload_data keys:
        - confidence_score, device_type, visitor_found
        - device_info, browser_info, geo_info
        - browser, os, user_agent, ip_address
        """
        update_fields = ["updated_at"]

        for field in [
            "confidence_score",
            "device_type",
            "visitor_found",
            "device_info",
            "browser_info",
            "geo_info",
            "browser",
            "os",
            "user_agent",
            "ip_address",
        ]:
            if field in payload_data:
                setattr(self, field, payload_data[field])
                update_fields.append(field)

        self.last_seen = timezone.now()
        update_fields.append("last_seen")
        self.save(update_fields=update_fields)

    # ── Contacts ─────────────────────────────────────────────────────

    def get_contacts(self) -> list:
        """Get all contacts linked to this fingerprint via FingerprintContact."""
        return list(self.contacts.select_related("content_type").all())

    # ── Fraud Detection ──────────────────────────────────────────────

    def get_fraud_signals(self) -> list[dict]:
        """Analyze fingerprint for fraud indicators."""
        signals = []

        # Check incognito
        if self.browser_info.get("incognito", False):
            signals.append(
                {
                    "type": "incognito",
                    "severity": "medium",
                    "description": "User is in incognito/private browsing mode",
                }
            )

        # Check low confidence
        if self.confidence_score < 0.5:
            signals.append(
                {
                    "type": "low_confidence",
                    "severity": "high",
                    "description": f"Low confidence score: {self.confidence_score}",
                }
            )

        # Check VPN (high accuracy radius indicates proxy/VPN)
        accuracy = self.geo_info.get("accuracy_radius", 0)
        if accuracy and accuracy > 1000:
            signals.append(
                {
                    "type": "vpn_suspected",
                    "severity": "high",
                    "description": f"High geo accuracy radius ({accuracy}km) suggests VPN/proxy",
                }
            )

        return signals

    def is_mobile_device(self) -> bool:
        """Check if this fingerprint is from a mobile device."""
        return self.device_type in ("mobile", "tablet")

    def get_browser_family(self) -> str:
        """Get simplified browser family name."""
        browser_lower = self.browser.lower()
        families = {
            "chrome": "Chrome",
            "firefox": "Firefox",
            "safari": "Safari",
            "edge": "Edge",
            "opera": "Opera",
            "brave": "Brave",
        }
        for key, family in families.items():
            if key in browser_lower:
                return family
        return self.browser or "Unknown"

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self, include_events: bool = False, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "hash": self.hash,
                "confidence_score": self.confidence_score,
                "device_type": self.device_type,
                "visitor_found": self.visitor_found,
                "device_info": self.device_info,
                "browser_info": self.browser_info,
                "geo_info": self.geo_info,
                "browser": self.browser,
                "browser_family": self.get_browser_family(),
                "os": self.os,
                "ip_address": self.ip_address,
                "first_seen": self.first_seen.isoformat() if self.first_seen else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "is_master": self.is_master,
                "is_mobile": self.is_mobile_device(),
                "identity_id": self.identity.public_id if self.identity else None,
                "fraud_signals": self.get_fraud_signals(),
            }
        )
        if include_events:
            data["events"] = [e.to_dict() for e in self.events.all()[:50]]
        return data


class FingerprintEvent(BaseModel):
    """
    An event tracked by a fingerprinted device.

    Records page views, form submissions, and other interactions.
    Events are linked to a specific fingerprint and optionally to a session.
    """

    PUBLIC_ID_PREFIX = "fpe"

    # Event types
    PAGE_VIEW = "page_view"
    FORM_SUBMIT = "form_submit"
    CLICK = "click"
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    fingerprint = models.ForeignKey(
        FingerprintIdentity,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Fingerprint",
    )
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Event type",
        help_text="page_view, form_submit, click, etc.",
    )
    page_url = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        verbose_name="Page URL",
    )
    timestamp = models.DateTimeField(
        db_index=True,
        verbose_name="Event timestamp",
    )
    user_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="User data",
        help_text="User-provided data (form fields, UTM params, etc.)",
    )
    event_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Event data",
        help_text="Technical event data (scroll position, element, etc.)",
    )
    session_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Session ID",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Fingerprint Event"
        verbose_name_plural = "Fingerprint Events"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["fingerprint", "-timestamp"]),
            models.Index(fields=["event_type", "-timestamp"]),
            models.Index(fields=["session_id"]),
        ]

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"

    # ── Factory Methods ──────────────────────────────────────────────

    @classmethod
    def record_pageview(
        cls,
        fingerprint: FingerprintIdentity,
        url: str,
        session_id: str | None = None,
        extra_data: dict | None = None,
    ) -> FingerprintEvent:
        """Record a page view event."""
        return cls.objects.create(
            fingerprint=fingerprint,
            event_type=cls.PAGE_VIEW,
            page_url=url,
            timestamp=timezone.now(),
            session_id=session_id,
            event_data=extra_data or {},
        )

    @classmethod
    def record_form_submission(
        cls,
        fingerprint: FingerprintIdentity,
        url: str,
        form_data: dict | None = None,
        session_id: str | None = None,
    ) -> FingerprintEvent:
        """Record a form submission event."""
        return cls.objects.create(
            fingerprint=fingerprint,
            event_type=cls.FORM_SUBMIT,
            page_url=url,
            timestamp=timezone.now(),
            user_data=form_data or {},
            session_id=session_id,
        )

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "event_type": self.event_type,
                "page_url": self.page_url,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "user_data": self.user_data,
                "event_data": self.event_data,
                "session_id": self.session_id,
                "fingerprint_id": self.fingerprint.public_id,
            }
        )
        return data


class FingerprintContact(BaseModel):
    """
    Polymorphic M2M association between a fingerprint and a contact
    (ContactEmail or ContactPhone).

    Uses Django's content types framework (GenericForeignKey) to link
    to either model without separate FK columns.
    """

    PUBLIC_ID_PREFIX = "fpc"

    # Verification status for the fingerprint-contact association
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    VERIFICATION_CHOICES = [
        (UNVERIFIED, "Unverified"),
        (PENDING, "Pending"),
        (VERIFIED, "Verified"),
    ]

    fingerprint = models.ForeignKey(
        FingerprintIdentity,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="Fingerprint",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label="contact_email", model="contactemail")
        | models.Q(app_label="contact_phone", model="contactphone"),
        verbose_name="Contact type",
    )
    object_id = models.PositiveBigIntegerField(
        verbose_name="Contact ID",
    )
    contact = GenericForeignKey("content_type", "object_id")

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default=UNVERIFIED,
        verbose_name="Verification status",
    )
    first_seen = models.DateTimeField(
        auto_now_add=True,
        verbose_name="First seen",
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name="Last seen",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "Fingerprint Contact"
        verbose_name_plural = "Fingerprint Contacts"
        unique_together = ("content_type", "object_id", "fingerprint")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["fingerprint"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self):
        return f"FP({self.fingerprint.hash[:8]}) -> {self.content_type.model}({self.object_id})"

    def to_dict(self, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "fingerprint_id": self.fingerprint.public_id,
                "contact_type": self.content_type.model if self.content_type else None,
                "verification_status": self.verification_status,
                "first_seen": self.first_seen.isoformat() if self.first_seen else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            }
        )
        return data
