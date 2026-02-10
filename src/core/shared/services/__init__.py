"""
Shared service layer.

Provides BaseService[T] generic class for CRUD operations
with built-in transaction management, validation, and audit.
"""

from .base import BaseService

__all__ = ["BaseService"]
