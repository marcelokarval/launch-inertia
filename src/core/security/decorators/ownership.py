"""
Ownership verification decorators and mixins for IDOR protection.

Provides:
- @require_ownership: Decorator for function-based views
- OwnershipMixin: Mixin for class-based detail/update/delete views
- OwnerFilterMixin: Mixin for class-based list views (auto-filter by owner)
- get_owned_object_or_404: Utility for mid-function ownership checks
"""

import functools
import logging
from typing import Callable, Optional, Type

from django.http import HttpRequest, HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.db import models

logger = logging.getLogger(__name__)


class RequireOwnershipError(PermissionDenied):
    """
    Custom PermissionDenied with metadata for security monitoring.

    Carries object_type and object_id for structured logging
    and security event detection.
    """

    def __init__(self, message: str, object_type: str = "", object_id: str = ""):
        super().__init__(message)
        self.object_type = object_type
        self.object_id = object_id


def _log_idor_attempt(
    request: HttpRequest,
    model: Type[models.Model],
    lookup_value: str,
    owner_id: Optional[int] = None,
) -> None:
    """Log an IDOR attempt and record it in the security event detector."""
    logger.warning(
        "IDOR attempt: User %s (IP: %s) tried to access %s.%s owned by user %s",
        request.user.id if request.user.is_authenticated else "anonymous",
        request.META.get("REMOTE_ADDR", "unknown"),
        model.__name__,
        lookup_value,
        owner_id or "None",
    )

    # Record in security event detector (fail-safe)
    try:
        from core.security.monitoring import security_detector

        security_detector.record_idor_attempt(
            user_id=str(request.user.id) if request.user.is_authenticated else None,
            ip_address=request.META.get("REMOTE_ADDR", "unknown"),
            path=request.path,
            target_id=f"{model.__name__}:{lookup_value}",
        )
    except Exception:
        # Security monitoring should never break the request
        pass


def require_ownership(
    model: Type[models.Model],
    lookup_field: str = "public_id",
    lookup_url_kwarg: Optional[str] = None,
    owner_field: str = "owner",
    allow_staff: bool = True,
    allow_superuser: bool = True,
    raise_404: bool = True,
):
    """
    Decorator to verify object ownership before allowing access.

    Prevents IDOR (Insecure Direct Object Reference) attacks by ensuring
    users can only access objects they own. The verified object is attached
    to `request.verified_object` so the view can use it without re-querying.

    Args:
        model: The Django model class.
        lookup_field: Model field to match against URL parameter.
        lookup_url_kwarg: URL parameter name (defaults to lookup_field).
        owner_field: Model field that references the owner (User FK).
        allow_staff: Whether to allow staff users to bypass ownership.
        allow_superuser: Whether to allow superusers to bypass ownership.
        raise_404: If True, raise 404 for non-existing objects; if False, raise 403.

    Usage::

        @login_required
        @require_ownership(Contact, owner_field="owner")
        def contact_detail(request, public_id):
            contact = request.verified_object  # Already fetched and verified
            ...
    """

    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            url_kwarg = lookup_url_kwarg or lookup_field
            lookup_value = kwargs.get(url_kwarg)

            if not lookup_value:
                logger.warning(
                    "Missing lookup value for %s: %s", model.__name__, url_kwarg
                )
                raise Http404("Object not found")

            # Fetch the object
            try:
                obj = model.objects.get(**{lookup_field: lookup_value})
            except model.DoesNotExist:
                logger.info(
                    "Object not found: %s.%s=%s",
                    model.__name__,
                    lookup_field,
                    lookup_value,
                )
                if raise_404:
                    raise Http404("Object not found")
                raise PermissionDenied("Access denied")

            # Attach to request for use in the view
            request.verified_object = obj

            # Superuser bypass
            if allow_superuser and request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Staff bypass
            if allow_staff and request.user.is_staff:
                return view_func(request, *args, **kwargs)

            # Verify ownership
            owner = getattr(obj, owner_field, None)
            if owner != request.user:
                _log_idor_attempt(
                    request,
                    model,
                    str(lookup_value),
                    owner_id=owner.id if owner else None,
                )
                raise RequireOwnershipError(
                    "You do not have permission to access this resource",
                    object_type=model.__name__,
                    object_id=str(lookup_value),
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def get_owned_object_or_404(
    model: Type[models.Model],
    user,
    lookup_field: str = "public_id",
    owner_field: str = "owner",
    allow_staff: bool = True,
    **lookup_kwargs,
) -> models.Model:
    """
    Utility function for mid-function ownership checks.

    Use when you need to verify ownership outside of the decorator pattern.

    Usage::

        contact = get_owned_object_or_404(
            Contact, request.user, public_id="con_abc123"
        )
    """
    try:
        obj = model.objects.get(**{lookup_field: lookup_kwargs.get(lookup_field)})
    except model.DoesNotExist:
        raise Http404(f"{model.__name__} not found")

    if allow_staff and user.is_staff:
        return obj

    if user.is_superuser:
        return obj

    owner = getattr(obj, owner_field, None)
    if owner != user:
        raise PermissionDenied("You do not have permission to access this resource")

    return obj


class OwnershipMixin:
    """
    Mixin for class-based detail/update/delete views to verify object ownership.

    Overrides get_object() to check that the current user owns the object
    before returning it.

    Usage::

        class ContactDetailView(OwnershipMixin, DetailView):
            model = Contact
            ownership_field = "owner"
            ownership_allow_staff = True
    """

    ownership_field: str = "owner"
    ownership_allow_staff: bool = True
    ownership_allow_superuser: bool = True

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if self.ownership_allow_superuser and self.request.user.is_superuser:
            return obj

        if self.ownership_allow_staff and self.request.user.is_staff:
            return obj

        owner = getattr(obj, self.ownership_field, None)
        if owner != self.request.user:
            _log_idor_attempt(
                self.request,
                type(obj),
                str(getattr(obj, "public_id", obj.pk)),
                owner_id=owner.id if owner else None,
            )
            raise PermissionDenied("You do not have permission to access this resource")

        return obj


class OwnerFilterMixin:
    """
    Mixin for class-based list views to auto-filter by owner.

    Overrides get_queryset() to only return records owned by the current user.
    Staff/superusers can optionally see all records.

    Usage::

        class ContactListView(OwnerFilterMixin, ListView):
            model = Contact
            owner_field = "owner"
            allow_staff_all = False  # Staff still only sees own records
    """

    owner_field: str = "owner"
    allow_staff_all: bool = False
    allow_superuser_all: bool = True

    def get_queryset(self):
        qs = super().get_queryset()

        if self.allow_superuser_all and self.request.user.is_superuser:
            return qs

        if self.allow_staff_all and self.request.user.is_staff:
            return qs

        return qs.filter(**{self.owner_field: self.request.user})
