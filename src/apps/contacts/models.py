"""
Contacts domain models.

Shared models used by the identity resolution system and future launch management.
The CRM Contact model has been eliminated — Identity is now the primary entity.
"""

from django.db import models

from core.shared.models.base import BaseModel, BaseTagModel


class Tag(BaseTagModel):
    """
    Tags for categorizing identities and launches.

    Inherits from BaseTagModel which provides:
    - name, slug, description, color fields
    - Auto-slug generation from name
    - to_dict() and to_public_dict() methods

    Used for:
    - Manual operator tags on Identities (e.g., "vip", "influencer")
    - Automatic launch tags (e.g., "WH0325", "ALUNO_WH0325")
    - Product tags (e.g., "MDL0325", "MDL0325_BUMP")
    """

    PUBLIC_ID_PREFIX = "tag"

    class Meta(BaseTagModel.Meta):
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class CustomFieldDefinition(BaseModel):
    """
    Defines custom fields that can be used across entities.

    This allows admins to create new fields without schema changes.
    Scope: will be associated with Launch in Phase 3.
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
