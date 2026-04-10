"""
Base model that combines all essential mixins.

All domain models should inherit from BaseModel to get:
- Timestamps (created_at, updated_at)
- Soft delete (is_deleted, deleted_at)
- Public ID (Stripe-like IDs)
- Activation status (is_active)
- Metadata (flexible JSON field)
- Version tracking (optimistic concurrency control)
"""

from typing import Any, Optional

from django.db import models

# ---------------------------------------------------------------------------
# Pyright: Django auto-generates `id: int` on models that don't declare a
# primary key. django-stubs doesn't always expose it. We annotate it here
# so that all BaseModel subclasses see `self.id` without warnings.
# ---------------------------------------------------------------------------

from ..managers import (
    BaseManager,
    AllObjectsManager,
    SearchManager,
    TimestampedManager,
)
from .mixins import (
    TimestampMixin,
    SoftDeleteMixin,
    PublicIDMixin,
    ActivatableMixin,
    MetadataMixin,
    VersionableMixin,
)


class BaseModel(
    TimestampMixin,
    SoftDeleteMixin,
    PublicIDMixin,
    ActivatableMixin,
    MetadataMixin,
    VersionableMixin,
    models.Model,
):
    """
    Abstract base model that all domain models should inherit from.

    Provides:
    - created_at, updated_at, age_days, is_new (TimestampMixin)
    - is_deleted, deleted_at, delete(), restore(), hard_delete() (SoftDeleteMixin)
    - public_id, get_public_id_prefix() (PublicIDMixin)
    - is_active, activate(), deactivate() (ActivatableMixin)
    - metadata, get_metadata(), set_metadata() (MetadataMixin)
    - version, check_version(), validate_version() (VersionableMixin)

    Managers:
    - objects: Default manager (excludes soft-deleted)
    - all_objects: Includes soft-deleted records
    - search: Specialized for search operations
    - timestamps: Specialized for timestamp queries

    Usage:
        class MyModel(BaseModel):
            PUBLIC_ID_PREFIX = "my"  # Results in IDs like my_a1b2c3d4
            name = models.CharField(max_length=100)

            class Meta(BaseModel.Meta):
                verbose_name = "My Model"
    """

    # Django auto PK — declared for pyright visibility
    id: int

    # Multiple managers for different use cases
    objects = BaseManager()
    all_objects = AllObjectsManager()
    search = SearchManager()
    timestamps = TimestampedManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        name = getattr(self, "name", None)
        if name:
            return str(name)
        title = getattr(self, "title", None)
        if title:
            return str(title)
        email = getattr(self, "email", None)
        if email:
            return str(email)
        return f"{self.__class__.__name__}({self.public_id})"

    def to_dict(
        self, include_metadata: bool = True, exclude_fields: Optional[list[str]] = None
    ) -> dict:
        """
        Convert model to dictionary.
        Override in subclasses for custom serialization.

        Args:
            include_metadata: Whether to include the metadata field
            exclude_fields: List of field names to exclude

        Returns:
            Dictionary representation of the model
        """
        exclude_fields = exclude_fields or []

        data = {
            "id": self.public_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "version": self.version,
        }

        if include_metadata and self.metadata and "metadata" not in exclude_fields:
            data["metadata"] = self.metadata

        # Remove excluded fields
        for field in exclude_fields:
            data.pop(field, None)

        return data

    def to_public_dict(self) -> dict:
        """
        Convert model to a dictionary safe for public API responses.
        Excludes sensitive fields like internal id, is_deleted, version.

        Override in subclasses to add model-specific public fields.
        """
        return {
            "id": self.public_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }

    def clone(self, **overrides) -> "BaseModel":
        """
        Create a copy of this instance with optional field overrides.
        The clone is not saved automatically.

        Args:
            **overrides: Field values to override in the clone

        Returns:
            New unsaved instance

        Usage:
            new_contact = contact.clone(email="new@example.com")
            new_contact.save()
        """
        # Get all field values except pk, public_id, and auto fields
        clone_data = {}
        for field in self._meta.fields:
            if field.name in (
                "id",
                "pk",
                "public_id",
                "created_at",
                "updated_at",
                "version",
            ):
                continue
            if field.primary_key:
                continue
            clone_data[field.name] = getattr(self, field.name)

        # Apply overrides
        clone_data.update(overrides)

        # Reset version and deleted status for clone
        clone_data["version"] = 1
        clone_data["is_deleted"] = False
        clone_data["deleted_at"] = None

        # Create new instance (public_id will be generated on save)
        return self.__class__(**clone_data)

    def refresh_and_check_version(self, expected_version: int) -> bool:
        """
        Refresh from database and check if version matches.
        Useful before performing updates.

        Args:
            expected_version: The version the client expects

        Returns:
            True if versions match, False if record was modified
        """
        self.refresh_from_db(fields=["version"])
        return self.version == expected_version


class BaseTagModel(BaseModel):
    """
    Abstract base model for tag-like entities (tags, categories, labels, etc.).

    Provides all BaseModel functionality plus:
    - name: Display name
    - slug: URL-safe identifier (auto-generated from name)
    - description: Optional description
    - color: Hex color code for UI display

    Usage:
        class Category(BaseTagModel):
            PUBLIC_ID_PREFIX = "cat"

            class Meta(BaseTagModel.Meta):
                verbose_name = "Category"
    """

    name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Name",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug",
        help_text="URL-safe identifier (auto-generated from name)",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        default="#6366f1",
        verbose_name="Color",
        help_text="Hex color code (e.g., #6366f1)",
    )

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            from django.utils.text import slugify

            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Ensure unique slug
            model = self.__class__
            while model.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def to_dict(self, **kwargs) -> dict:
        """Include tag-specific fields in dict representation."""
        data = super().to_dict(**kwargs)
        data.update(
            {
                "name": self.name,
                "slug": self.slug,
                "description": self.description,
                "color": self.color,
            }
        )
        return data

    def to_public_dict(self) -> dict:
        """Public representation of tag."""
        data = super().to_public_dict()
        data.update(
            {
                "name": self.name,
                "slug": self.slug,
                "color": self.color,
            }
        )
        return data
