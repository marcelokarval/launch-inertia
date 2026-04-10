"""
Shared models package for Launch Inertia.

This package provides the foundation for all domain models.

Usage:
    from core.shared.models import BaseModel, BaseTagModel
    from core.shared.models import TimestampMixin, SoftDeleteMixin, ...
    from core.shared.models import BaseManager, AllObjectsManager, ...
"""

# Base models
from .base import BaseModel, BaseTagModel

# Mixins
from .mixins import (
    TimestampMixin,
    PublicIDMixin,
    SoftDeleteMixin,
    ActivatableMixin,
    MetadataMixin,
    VersionableMixin,
)

# Managers
from ..managers import (
    BaseManager,
    AllObjectsManager,
    SearchManager,
    TimestampedManager,
    BaseQuerySet,
)

__all__ = [
    # Base models
    "BaseModel",
    "BaseTagModel",
    # Mixins
    "TimestampMixin",
    "PublicIDMixin",
    "SoftDeleteMixin",
    "ActivatableMixin",
    "MetadataMixin",
    "VersionableMixin",
    # Managers
    "BaseManager",
    "AllObjectsManager",
    "SearchManager",
    "TimestampedManager",
    "BaseQuerySet",
]
