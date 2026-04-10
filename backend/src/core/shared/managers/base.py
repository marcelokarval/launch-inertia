"""
Custom managers and querysets for BaseModel.

Provides filtering methods that respect soft delete and activation status.
All methods use hasattr() checks to work safely with models that don't have all mixins.

IMPORTANT: Use lazy imports inside methods to avoid AppRegistryNotReady errors.
"""
from typing import TYPE_CHECKING, Optional

from django.db import models
from django.db.models import Q

if TYPE_CHECKING:
    from ..models.base import BaseModel


class BaseQuerySet(models.QuerySet):
    """
    Custom QuerySet that provides common filtering methods.
    All methods check if the model has the required field before filtering.
    """

    def active(self) -> "BaseQuerySet":
        """Return only active records (if model has ActivatableMixin)."""
        if hasattr(self.model, "is_active"):
            return self.filter(is_active=True)
        return self

    def inactive(self) -> "BaseQuerySet":
        """Return only inactive records (if model has ActivatableMixin)."""
        if hasattr(self.model, "is_active"):
            return self.filter(is_active=False)
        return self

    def not_deleted(self) -> "BaseQuerySet":
        """Return only non-deleted records (if model has SoftDeleteMixin)."""
        if hasattr(self.model, "is_deleted"):
            return self.filter(is_deleted=False)
        return self

    def deleted(self) -> "BaseQuerySet":
        """Return only soft-deleted records (if model has SoftDeleteMixin)."""
        if hasattr(self.model, "is_deleted"):
            return self.filter(is_deleted=True)
        return self

    def with_deleted(self) -> "BaseQuerySet":
        """Return all records including soft-deleted ones."""
        return self.all()

    def by_public_id(self, public_id: str) -> "BaseQuerySet":
        """Filter by public ID (if model has PublicIDMixin)."""
        if hasattr(self.model, "public_id"):
            return self.filter(public_id=public_id)
        return self.none()

    def recent(self, days: int = 30) -> "BaseQuerySet":
        """Return records created in the last N days."""
        from datetime import timedelta
        from django.utils import timezone

        if hasattr(self.model, "created_at"):
            threshold = timezone.now() - timedelta(days=days)
            return self.filter(created_at__gte=threshold)
        return self

    def created_after(self, dt) -> "BaseQuerySet":
        """Return records created after the given datetime."""
        if hasattr(self.model, "created_at"):
            return self.filter(created_at__gte=dt)
        return self

    def created_before(self, dt) -> "BaseQuerySet":
        """Return records created before the given datetime."""
        if hasattr(self.model, "created_at"):
            return self.filter(created_at__lte=dt)
        return self

    def created_between(self, start_dt, end_dt) -> "BaseQuerySet":
        """Return records created between two datetimes."""
        if hasattr(self.model, "created_at"):
            return self.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        return self

    def order_by_created(self, ascending: bool = False) -> "BaseQuerySet":
        """Order by creation date."""
        if hasattr(self.model, "created_at"):
            field = "created_at" if ascending else "-created_at"
            return self.order_by(field)
        return self

    def order_by_updated(self, ascending: bool = False) -> "BaseQuerySet":
        """Order by update date."""
        if hasattr(self.model, "updated_at"):
            field = "updated_at" if ascending else "-updated_at"
            return self.order_by(field)
        return self

    def search(self, query: str, fields: list[str]) -> "BaseQuerySet":
        """
        Search across multiple fields using icontains.

        Usage:
            Model.objects.search("john", ["name", "email"])
        """
        if not query or not fields:
            return self

        q_objects = Q()
        for field in fields:
            q_objects |= Q(**{f"{field}__icontains": query})

        return self.filter(q_objects)


class BaseManager(models.Manager):
    """
    Default manager that uses BaseQuerySet and excludes soft-deleted records by default.
    """

    def get_queryset(self) -> BaseQuerySet:
        """Return queryset that excludes soft-deleted records by default."""
        return BaseQuerySet(self.model, using=self._db).not_deleted()

    def active(self) -> BaseQuerySet:
        """Return only active records."""
        return self.get_queryset().active()

    def inactive(self) -> BaseQuerySet:
        """Return only inactive records."""
        return self.get_queryset().inactive()

    def with_deleted(self) -> BaseQuerySet:
        """Return all records including soft-deleted ones."""
        return BaseQuerySet(self.model, using=self._db)

    def deleted(self) -> BaseQuerySet:
        """Return only soft-deleted records."""
        return BaseQuerySet(self.model, using=self._db).deleted()

    def recent(self, days: int = 30) -> BaseQuerySet:
        """Return records created in the last N days."""
        return self.get_queryset().recent(days)

    def by_public_id(self, public_id: str):
        """Get a single record by public ID."""
        return self.get_queryset().by_public_id(public_id).first()

    def get_by_public_id(self, public_id: str):
        """Get a single record by public ID (alias for by_public_id)."""
        return self.by_public_id(public_id)

    def order_by_created(self, ascending: bool = False) -> BaseQuerySet:
        """Order by creation date."""
        return self.get_queryset().order_by_created(ascending)

    def order_by_updated(self, ascending: bool = False) -> BaseQuerySet:
        """Order by update date."""
        return self.get_queryset().order_by_updated(ascending)

    def get_or_none(self, **kwargs):
        """
        Get a single object or return None if not found.
        More elegant than try/except DoesNotExist.
        """
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class AllObjectsManager(models.Manager):
    """
    Manager that includes soft-deleted records.
    Use this when you need to access all records regardless of deletion status.

    Usage:
        Model.all_objects.all()  # Includes soft-deleted
        Model.all_objects.deleted()  # Only soft-deleted
    """

    def get_queryset(self) -> BaseQuerySet:
        """Return queryset including all records."""
        return BaseQuerySet(self.model, using=self._db)

    def active(self) -> BaseQuerySet:
        """Return only active records (including soft-deleted active)."""
        return self.get_queryset().active()

    def inactive(self) -> BaseQuerySet:
        """Return only inactive records."""
        return self.get_queryset().inactive()

    def deleted(self) -> BaseQuerySet:
        """Return only soft-deleted records."""
        return self.get_queryset().deleted()

    def not_deleted(self) -> BaseQuerySet:
        """Return only non-deleted records."""
        return self.get_queryset().not_deleted()


class SearchManager(models.Manager):
    """
    Manager specialized for search operations.

    Usage:
        Model.search.search("john", ["name", "email"])
        Model.search.search_by_terms(name="john", email__icontains="example")
    """

    def get_queryset(self) -> BaseQuerySet:
        """Return base queryset excluding soft-deleted records."""
        return BaseQuerySet(self.model, using=self._db).not_deleted()

    def search(self, query: str, fields: Optional[list[str]] = None) -> BaseQuerySet:
        """
        Search across multiple fields using icontains.

        Args:
            query: The search string
            fields: List of field names to search. If None, searches common fields.

        Usage:
            User.search.search("john", ["first_name", "last_name", "email"])
        """
        if not query:
            return self.get_queryset()

        # Default searchable fields if none provided
        if fields is None:
            fields = self._get_default_search_fields()

        return self.get_queryset().search(query, fields)

    def search_by_terms(self, **terms) -> BaseQuerySet:
        """
        Search by specific field terms.

        Args:
            **terms: Field lookups (supports Django field lookups like __icontains)

        Usage:
            User.search.search_by_terms(first_name__icontains="john", is_active=True)
        """
        return self.get_queryset().filter(**terms)

    def _get_default_search_fields(self) -> list[str]:
        """Get default searchable fields based on model."""
        common_fields = ["name", "title", "email", "description"]
        return [f for f in common_fields if hasattr(self.model, f)]


class TimestampedManager(models.Manager):
    """
    Manager specialized for timestamp-based queries.

    Usage:
        Model.timestamps.created_today()
        Model.timestamps.created_this_week()
        Model.timestamps.updated_since(some_datetime)
    """

    def get_queryset(self) -> BaseQuerySet:
        """Return base queryset excluding soft-deleted records."""
        return BaseQuerySet(self.model, using=self._db).not_deleted()

    def created_today(self) -> BaseQuerySet:
        """Return records created today."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.get_queryset().filter(
            created_at__date=today
        )

    def created_this_week(self) -> BaseQuerySet:
        """Return records created in the current week."""
        from datetime import timedelta
        from django.utils import timezone
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        return self.get_queryset().filter(
            created_at__date__gte=start_of_week
        )

    def created_this_month(self) -> BaseQuerySet:
        """Return records created in the current month."""
        from django.utils import timezone
        now = timezone.now()
        return self.get_queryset().filter(
            created_at__year=now.year,
            created_at__month=now.month
        )

    def created_between(self, start_date, end_date) -> BaseQuerySet:
        """Return records created between two dates."""
        return self.get_queryset().created_between(start_date, end_date)

    def updated_since(self, dt) -> BaseQuerySet:
        """Return records updated since the given datetime."""
        if hasattr(self.model, "updated_at"):
            return self.get_queryset().filter(updated_at__gte=dt)
        return self.get_queryset()

    def recent(self, days: int = 30) -> BaseQuerySet:
        """Return records created in the last N days."""
        return self.get_queryset().recent(days)
