"""
Contacts domain models.

CRM models for managing contacts, companies, tags, and custom fields.
"""
from django.db import models
from django.conf import settings

from core.shared.models.base import BaseModel, BaseTagModel


class Tag(BaseTagModel):
    """
    Tags for categorizing contacts.

    Inherits from BaseTagModel which provides:
    - name, slug, description, color fields
    - Auto-slug generation from name
    - to_dict() and to_public_dict() methods
    """

    PUBLIC_ID_PREFIX = "tag"

    class Meta(BaseTagModel.Meta):
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class Contact(BaseModel):
    """
    Main contact model for CRM.

    Represents a person or entity with contact information.
    Designed to grow with additional fields and relationships.
    """

    PUBLIC_ID_PREFIX = "con"

    # Basic info
    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True, db_index=True)

    # Company info
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=100, blank=True)

    # Source tracking
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual Entry"
        IMPORT = "import", "CSV Import"
        FORM = "form", "Form Submission"
        API = "api", "API"
        INTEGRATION = "integration", "Integration"

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )

    # Status
    class Status(models.TextChoices):
        LEAD = "lead", "Lead"
        PROSPECT = "prospect", "Prospect"
        CUSTOMER = "customer", "Customer"
        CHURNED = "churned", "Churned"
        INACTIVE = "inactive", "Inactive"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.LEAD,
        db_index=True,
    )

    # Lead scoring
    lead_score = models.PositiveIntegerField(default=0)

    # Categorization
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")

    # Custom fields (flexible JSON storage)
    custom_fields = models.JSONField(default=dict, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_contacts",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contacts",
    )

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Phone verification
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    # First/Last seen
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return self.name or self.email or self.phone or f"Contact {self.public_id}"

    def to_dict(self, include_details: bool = False) -> dict:
        """Serialize contact for Inertia props."""
        data = {
            "id": self.public_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "status": self.status,
            "lead_score": self.lead_score,
            "source": self.source,
            "email_verified": self.email_verified,
            "phone_verified": self.phone_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": [{"id": t.public_id, "name": t.name, "color": t.color} for t in self.tags.all()],
        }

        if include_details:
            data.update({
                "notes": self.notes,
                "custom_fields": self.custom_fields,
                "owner": self.owner.to_dict() if self.owner else None,
                "created_by": self.created_by.to_dict() if self.created_by else None,
                "metadata": self.metadata,
            })

        return data


class ContactEmail(BaseModel):
    """Additional email addresses for a contact."""

    PUBLIC_ID_PREFIX = "cem"

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="emails",
    )
    email = models.EmailField()
    label = models.CharField(max_length=50, default="work")  # work, personal, other
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Email"
        verbose_name_plural = "Contact Emails"
        unique_together = [("contact", "email")]

    def __str__(self):
        return self.email


class ContactPhone(BaseModel):
    """Additional phone numbers for a contact."""

    PUBLIC_ID_PREFIX = "cph"

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="phones",
    )
    phone = models.CharField(max_length=50)
    label = models.CharField(max_length=50, default="mobile")  # mobile, work, home, other
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Phone"
        verbose_name_plural = "Contact Phones"
        unique_together = [("contact", "phone")]

    def __str__(self):
        return self.phone


class ContactNote(BaseModel):
    """Notes and activity log for contacts."""

    PUBLIC_ID_PREFIX = "cnt"

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="contact_notes",
    )
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class NoteType(models.TextChoices):
        NOTE = "note", "Note"
        CALL = "call", "Call"
        EMAIL = "email", "Email"
        MEETING = "meeting", "Meeting"
        TASK = "task", "Task"

    note_type = models.CharField(
        max_length=20,
        choices=NoteType.choices,
        default=NoteType.NOTE,
    )

    class Meta:
        verbose_name = "Contact Note"
        verbose_name_plural = "Contact Notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.note_type}: {self.content[:50]}"


class CustomFieldDefinition(BaseModel):
    """
    Defines custom fields that can be used across contacts.

    This allows admins to create new fields without schema changes.
    """

    PUBLIC_ID_PREFIX = "cfd"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        DATETIME = "datetime", "Date & Time"
        BOOLEAN = "boolean", "Yes/No"
        SELECT = "select", "Dropdown"
        MULTISELECT = "multiselect", "Multi-select"
        URL = "url", "URL"
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"

    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT,
    )

    # For select/multiselect fields
    options = models.JSONField(default=list, blank=True)

    # Validation
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)

    # Display
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Custom Field"
        verbose_name_plural = "Custom Fields"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
