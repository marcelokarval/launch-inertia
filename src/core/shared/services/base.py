"""
Base service class with generic CRUD operations.

All write operations are wrapped in @transaction.atomic.
Read operations leverage the model's custom managers.

Usage:
    class ContactService(BaseService[Contact]):
        model = Contact

    service = ContactService(user=request.user)
    contact = service.create(name="John", email="john@example.com")
    contacts = service.get_all(status="lead")
"""

import logging
from typing import Any, Generic, Optional, TypeVar

from django.core.exceptions import ValidationError
from django.db import models, transaction

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=models.Model)


class BaseService(Generic[T]):
    """
    Generic base service providing standard CRUD operations.

    Features:
    - User context for audit and ownership
    - Atomic transactions on all writes
    - full_clean() validation before save
    - Soft delete by default, hard delete opt-in
    - Logging of all operations
    """

    model: type[T]

    def __init__(self, user=None):
        """
        Initialize service with optional user context.

        Args:
            user: The authenticated user performing the operations.
                  Used for audit trails and ownership assignment.
        """
        self.user = user

    # ── Read Operations ─────────────────────────────────────────────────

    def get_by_id(self, pk: int) -> Optional[T]:
        """Get a record by primary key. Returns None if not found."""
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get_by_public_id(self, public_id: str) -> Optional[T]:
        """Get a record by public_id. Returns None if not found."""
        try:
            return self.model.objects.get(public_id=public_id)
        except self.model.DoesNotExist:
            return None

    def get_by_public_id_or_404(self, public_id: str) -> T:
        """Get a record by public_id or raise Http404."""
        from django.http import Http404

        instance = self.get_by_public_id(public_id)
        if instance is None:
            raise Http404(f"{self.model.__name__} not found: {public_id}")
        return instance

    def get_all(self, **filters) -> models.QuerySet[T]:
        """Get all records matching filters (excludes soft-deleted)."""
        return self.model.objects.filter(**filters)

    def get_active(self, **filters) -> models.QuerySet[T]:
        """Get only active records (not deleted, is_active=True)."""
        qs = self.model.objects
        if hasattr(qs, "active"):
            return qs.active().filter(**filters)  # type: ignore[attr-defined]
        return qs.filter(is_active=True, **filters)

    def get_queryset(self, **filters) -> models.QuerySet[T]:
        """Get base queryset. Override in subclasses for custom filtering."""
        return self.model.objects.filter(**filters)

    def search(
        self, query: str, fields: Optional[list[str]] = None
    ) -> models.QuerySet[T]:
        """
        Full-text search across model fields.
        Uses the SearchManager if available.
        """
        model_search = getattr(self.model, "search", None)
        if model_search is not None and hasattr(model_search, "search"):
            return model_search.search(query, fields=fields)
        # Fallback: basic filter on common fields
        from django.db.models import Q

        q = Q()
        search_fields = fields or ["name", "email", "title"]
        for field in search_fields:
            if hasattr(self.model, field) or any(
                f.name == field for f in self.model._meta.fields
            ):
                q |= Q(**{f"{field}__icontains": query})
        return self.model.objects.filter(q)

    def exists(self, **filters) -> bool:
        """Check if any records match the filters."""
        return self.model.objects.filter(**filters).exists()

    def count(self, **filters) -> int:
        """Count records matching filters."""
        return self.model.objects.filter(**filters).count()

    # ── Write Operations ────────────────────────────────────────────────

    @transaction.atomic
    def create(self, **kwargs) -> T:
        """
        Create a new record.

        Runs full_clean() for validation before saving.
        Wrapped in a transaction.

        Args:
            **kwargs: Field values for the new record

        Returns:
            The created instance

        Raises:
            ValidationError: If validation fails
        """
        instance = self.model(**kwargs)

        try:
            instance.full_clean()
        except ValidationError:
            logger.warning(
                "Validation failed on %s.create: %s",
                self.model.__name__,
                kwargs.get("name", kwargs.get("email", "unknown")),
            )
            raise

        instance.save()
        logger.info(
            "Created %s (id=%s) by user=%s",
            self.model.__name__,
            getattr(instance, "public_id", instance.pk),
            self.user,
        )
        return instance

    @transaction.atomic
    def update(self, instance: T, **kwargs) -> T:
        """
        Update an existing record.

        Runs full_clean() for validation before saving.
        Wrapped in a transaction.

        Args:
            instance: The model instance to update
            **kwargs: Field values to update

        Returns:
            The updated instance

        Raises:
            ValidationError: If validation fails
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)

        try:
            instance.full_clean()
        except ValidationError:
            logger.warning(
                "Validation failed on %s.update (id=%s)",
                self.model.__name__,
                getattr(instance, "public_id", instance.pk),
            )
            raise

        instance.save()
        logger.info(
            "Updated %s (id=%s) by user=%s",
            self.model.__name__,
            getattr(instance, "public_id", instance.pk),
            self.user,
        )
        return instance

    @transaction.atomic
    def delete(self, instance: T, hard: bool = False) -> None:
        """
        Delete a record (soft delete by default).

        Args:
            instance: The model instance to delete
            hard: If True, permanently delete. Otherwise soft-delete.
        """
        public_id = getattr(instance, "public_id", instance.pk)

        if hard:
            instance.delete(hard=True) if hasattr(  # type: ignore[call-arg]
                instance.delete, "__code__"
            ) and "hard" in instance.delete.__code__.co_varnames else instance.delete()
            logger.warning(
                "Hard deleted %s (id=%s) by user=%s",
                self.model.__name__,
                public_id,
                self.user,
            )
        else:
            if hasattr(instance, "is_deleted"):
                instance.delete()  # SoftDeleteMixin's soft delete
            else:
                instance.delete()  # Regular Django delete
            logger.info(
                "Soft deleted %s (id=%s) by user=%s",
                self.model.__name__,
                public_id,
                self.user,
            )

    @transaction.atomic
    def bulk_create(self, items: list[dict[str, Any]]) -> list[T]:
        """
        Create multiple records in a single transaction.

        Args:
            items: List of dicts with field values

        Returns:
            List of created instances
        """
        instances = [self.model(**data) for data in items]

        # Validate all before saving
        for instance in instances:
            instance.full_clean()

        created = self.model.objects.bulk_create(instances)
        logger.info(
            "Bulk created %d %s records by user=%s",
            len(created),
            self.model.__name__,
            self.user,
        )
        return created

    @transaction.atomic
    def bulk_update(self, queryset: models.QuerySet[T], **kwargs) -> int:
        """
        Bulk update records matching a queryset.

        Args:
            queryset: QuerySet of records to update
            **kwargs: Field values to update

        Returns:
            Number of records updated
        """
        count = queryset.update(**kwargs)
        logger.info(
            "Bulk updated %d %s records by user=%s",
            count,
            self.model.__name__,
            self.user,
        )
        return count

    # ── Ownership Helpers ───────────────────────────────────────────────

    # Fields checked (in priority order) to determine the ownership FK.
    OWNERSHIP_FIELDS = ("owner", "user", "created_by", "recipient")

    def _get_owner_field(self) -> Optional[str]:
        """
        Return the name of the ownership FK on the model, or None.

        Checks OWNERSHIP_FIELDS in order and returns the first match.
        """
        model_field_names = {f.name for f in self.model._meta.fields}
        for field_name in self.OWNERSHIP_FIELDS:
            if field_name in model_field_names:
                return field_name
        return None

    def get_for_user(self, **filters) -> models.QuerySet[T]:
        """
        Get records owned by the current user.

        Returns an empty queryset if:
        - No user is set on the service
        - The model has no recognized ownership field

        This prevents silent data leakage when ownership fields are missing.
        """
        if not self.user:
            return self.model.objects.none()

        owner_field = self._get_owner_field()
        if owner_field is None:
            logger.warning(
                "No ownership field found on %s. Returning empty queryset "
                "to prevent data leakage. Add an ownership field or override "
                "get_for_user() in the subclass.",
                self.model.__name__,
            )
            return self.model.objects.none()

        return self.model.objects.filter(**{owner_field: self.user, **filters})

    def get_for_user_by_public_id(self, public_id: str) -> Optional[T]:
        """Get a record by public_id ensuring it belongs to the current user."""
        qs = self.get_for_user()
        try:
            return qs.get(public_id=public_id)
        except self.model.DoesNotExist:
            return None

    def get_for_user_by_public_id_or_404(self, public_id: str) -> T:
        """
        Get a record by public_id ensuring it belongs to the current user.
        Raises Http404 if not found or not owned by the user.
        """
        from django.http import Http404

        instance = self.get_for_user_by_public_id(public_id)
        if instance is None:
            raise Http404(f"{self.model.__name__} not found: {public_id}")
        return instance
