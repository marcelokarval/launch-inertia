"""
Reusable model mixins for Django models.

These mixins provide common functionality that can be composed together
to create feature-rich models.

IMPORTANT: All imports that depend on Django being fully loaded
should be done inside methods (lazy imports) to avoid AppRegistryNotReady errors.
"""
import secrets
import string
from typing import Any, Optional

from django.db import models


class TimestampMixin(models.Model):
    """
    Adds created_at and updated_at fields to track record lifecycle.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        abstract = True

    @property
    def age_days(self) -> int:
        """Get the age of this record in days."""
        from django.utils import timezone  # Lazy import
        if self.created_at:
            return (timezone.now() - self.created_at).days
        return 0

    @property
    def is_new(self) -> bool:
        """Check if record was created in the last 24 hours."""
        return self.age_days == 0


class SoftDeleteMixin(models.Model):
    """
    Implements soft delete pattern - records are marked as deleted
    instead of being physically removed from the database.
    """
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Is deleted",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deleted at",
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard: bool = False):
        """
        Soft delete by default. Use hard=True for permanent deletion.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        from django.utils import timezone  # Lazy import
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the record."""
        return super().delete(using=using, keep_parents=keep_parents)


class PublicIDMixin(models.Model):
    """
    Generates Stripe-like public IDs for external reference.

    Format: {prefix}_{random_string}
    Example: usr_a1b2c3d4e5f6, con_x9y8z7w6v5u4
    """
    public_id = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Public ID",
    )

    # Override in subclass to set prefix
    PUBLIC_ID_PREFIX: str = "obj"
    PUBLIC_ID_LENGTH: int = 16

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = self._generate_public_id()
        super().save(*args, **kwargs)

    def _generate_public_id(self) -> str:
        """Generate a unique public ID with model-specific prefix."""
        prefix = self.get_public_id_prefix()
        chars = string.ascii_lowercase + string.digits
        random_part = "".join(secrets.choice(chars) for _ in range(self.PUBLIC_ID_LENGTH))
        return f"{prefix}_{random_part}"

    def get_public_id_prefix(self) -> str:
        """
        Get the prefix for public IDs.
        Override this method in subclasses for dynamic prefixes.
        """
        return self.PUBLIC_ID_PREFIX

    @classmethod
    def get_by_public_id(cls, public_id: str):
        """Retrieve an object by its public ID."""
        return cls.objects.filter(public_id=public_id).first()


class ActivatableMixin(models.Model):
    """
    Adds activation/deactivation status tracking.
    """
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Is active",
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Activated at",
    )
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Deactivated at",
    )

    class Meta:
        abstract = True

    def activate(self) -> None:
        """Activate the record."""
        from django.utils import timezone  # Lazy import
        self.is_active = True
        self.activated_at = timezone.now()
        self.deactivated_at = None
        self.save(update_fields=["is_active", "activated_at", "deactivated_at"])

    def deactivate(self) -> None:
        """Deactivate the record."""
        from django.utils import timezone  # Lazy import
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save(update_fields=["is_active", "deactivated_at"])


class MetadataMixin(models.Model):
    """
    Adds a flexible JSON metadata field for storing additional data
    without schema changes.
    """
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadata",
        help_text="Additional data stored as JSON",
    )

    class Meta:
        abstract = True

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a value from metadata."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a value in metadata."""
        self.metadata[key] = value
        self.save(update_fields=["metadata"])

    def update_metadata(self, data: dict) -> None:
        """Update metadata with multiple key-value pairs."""
        self.metadata.update(data)
        self.save(update_fields=["metadata"])

    def remove_metadata(self, key: str) -> None:
        """Remove a key from metadata."""
        if key in self.metadata:
            del self.metadata[key]
            self.save(update_fields=["metadata"])

    def has_metadata(self, key: str) -> bool:
        """Check if a key exists in metadata."""
        return key in self.metadata


class VersionableMixin(models.Model):
    """
    Adds version tracking for optimistic concurrency control.

    This prevents lost updates when multiple users edit the same record.
    The version is incremented on each save, and validation can check
    if the record was modified since it was loaded.
    """
    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Version",
        help_text="Record version for optimistic locking",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Increment version on each save."""
        if self.pk:  # Only increment for updates, not creates
            self.version += 1
        super().save(*args, **kwargs)

    def check_version(self, expected_version: int) -> bool:
        """
        Check if the current version matches the expected version.

        Use this before saving to detect concurrent modifications.

        Args:
            expected_version: The version the client expects

        Returns:
            True if versions match, False if record was modified
        """
        return self.version == expected_version

    def validate_version(self, expected_version: int) -> None:
        """
        Validate version and raise exception if mismatch.

        Args:
            expected_version: The version the client expects

        Raises:
            ValidationError: If versions don't match
        """
        from django.core.exceptions import ValidationError
        if not self.check_version(expected_version):
            raise ValidationError(
                f"Record was modified by another user. "
                f"Expected version {expected_version}, but current version is {self.version}."
            )
