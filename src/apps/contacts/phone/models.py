"""
Contact phone model.

Tracks phone numbers captured from registration forms, imports, or API.
Each phone is linked to an Identity for cross-channel resolution.
Supports Brazilian phone patterns, WhatsApp detection, and E.164 normalization.
"""

import re

from django.db import models

from core.shared.models.base import BaseModel


class ContactPhone(BaseModel):
    """
    A phone number captured as a contact channel.

    Fields from legacy ContactBase (abstract) + ContactPhone (concrete):
    - value: normalized phone (E.164 when possible)
    - original_value: raw input from the user
    - country_code: extracted/detected country code
    - is_verified: manual/automatic verification
    - identity: FK to the unified Identity

    Lifecycle metadata stored in the `metadata` JSONField (from BaseModel):
    - verification_code: for SMS verification flow
    - verification_expiry: when verification code expires
    - carrier: detected carrier name
    - phone_type: mobile, landline, voip
    - is_whatsapp: whether the number has WhatsApp
    - is_sms_capable: whether SMS delivery is possible
    """

    PUBLIC_ID_PREFIX = "cph"

    # Phone type constants
    MOBILE = "mobile"
    LANDLINE = "landline"
    VOIP = "voip"
    UNKNOWN = "unknown"
    PHONE_TYPE_CHOICES = [
        (MOBILE, "Mobile"),
        (LANDLINE, "Landline"),
        (VOIP, "VoIP"),
        (UNKNOWN, "Unknown"),
    ]

    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="phone_contacts",
        verbose_name="Identity",
    )
    value = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Phone number",
        help_text="Normalized phone number (E.164 format when possible)",
    )
    original_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Original value",
        help_text="Raw phone as entered by the user before normalization",
    )
    country_code = models.CharField(
        max_length=10,
        blank=True,
        default="55",
        verbose_name="Country code",
        help_text="Phone country code (default: 55 for Brazil)",
    )
    phone_type = models.CharField(
        max_length=20,
        choices=PHONE_TYPE_CHOICES,
        default=UNKNOWN,
        verbose_name="Phone type",
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
    is_whatsapp = models.BooleanField(
        default=False,
        verbose_name="Is WhatsApp",
        help_text="Whether this number is registered on WhatsApp",
    )
    is_sms_capable = models.BooleanField(
        default=True,
        verbose_name="SMS capable",
        help_text="Whether SMS can be delivered to this number",
    )
    is_dnc = models.BooleanField(
        default=False,
        verbose_name="Do not contact",
        help_text="Whether this number is on a Do Not Contact list",
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
    searchable_fields = ["value", "original_value", "country_code"]

    class Meta(BaseModel.Meta):
        verbose_name = "Contact Phone"
        verbose_name_plural = "Contact Phones"
        indexes = [
            models.Index(fields=["is_verified"]),
            models.Index(fields=["identity"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["phone_type"]),
            models.Index(fields=["first_seen"]),
        ]

    def __str__(self):
        return self.value

    # ── Normalization ────────────────────────────────────────────────

    def normalize(self) -> None:
        """
        Normalize phone number to a consistent format.

        Attempts E.164 format via phonenumbers library.
        Falls back to digit-only normalization with country code prefix.
        """
        if not self.value:
            return

        try:
            import phonenumbers

            parsed = phonenumbers.parse(self.value, "BR")
            if phonenumbers.is_valid_number(parsed):
                self.value = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
                self.country_code = str(parsed.country_code)
                return
        except (ImportError, Exception):
            pass

        # Fallback: strip non-digits, prepend country code
        digits = re.sub(r"[^\d]", "", self.value)
        if digits and not digits.startswith(self.country_code):
            digits = f"{self.country_code}{digits}"
        if digits:
            self.value = f"+{digits}"

    def save(self, *args, **kwargs):
        """Auto-normalize, preserve original value, and detect type on save."""
        if not self.original_value and self.value:
            self.original_value = self.value
        self.normalize()
        if self.phone_type == self.UNKNOWN:
            self.phone_type = self.detect_type()
        super().save(*args, **kwargs)

    # ── Verification ─────────────────────────────────────────────────

    def verify(self) -> None:
        """Mark this phone as verified."""
        from django.utils import timezone

        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])

    def unverify(self) -> None:
        """Remove verification status."""
        self.is_verified = False
        self.verified_at = None
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])

    # ── Type Detection ───────────────────────────────────────────────

    def detect_type(self) -> str:
        """
        Detect phone type based on Brazilian numbering patterns.

        Brazilian mobile numbers:
        - Start with 9 after DDD (2 digits)
        - Total 11 digits (DDD + 9 + 8 digits)

        Brazilian landlines:
        - Start with 2-5 after DDD
        - Total 10 digits (DDD + 8 digits)
        """
        digits = re.sub(r"[^\d]", "", self.value)

        # Remove country code if present
        if digits.startswith("55"):
            digits = digits[2:]

        if len(digits) == 11 and digits[2] == "9":
            return self.MOBILE
        elif len(digits) == 10:
            return self.LANDLINE
        else:
            return self.UNKNOWN

    # ── Display ──────────────────────────────────────────────────────

    def format_for_display(self) -> str:
        """Format phone for Brazilian display: (XX) XXXXX-XXXX or (XX) XXXX-XXXX."""
        digits = re.sub(r"[^\d]", "", self.value)
        if digits.startswith("55"):
            digits = digits[2:]

        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return self.value

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self, **kwargs) -> dict:
        """Serialize for Inertia props."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "value": self.value,
                "original_value": self.original_value,
                "country_code": self.country_code,
                "phone_type": self.phone_type,
                "display_value": self.format_for_display(),
                "is_verified": self.is_verified,
                "verified_at": self.verified_at.isoformat()
                if self.verified_at
                else None,
                "is_whatsapp": self.is_whatsapp,
                "is_sms_capable": self.is_sms_capable,
                "is_dnc": self.is_dnc,
                "first_seen": self.first_seen.isoformat() if self.first_seen else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "identity_id": self.identity.public_id if self.identity else None,
            }
        )
        return data
