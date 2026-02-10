"""
Contact service layer.

Encapsulates all business logic for contact CRUD operations,
keeping views thin and focused on HTTP/Inertia concerns.

All read operations filter by the current user's ownership to prevent IDOR.
"""

import logging
from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.db import models, transaction

from core.shared.services.base import BaseService
from ..forms import ContactForm
from ..models import Contact

logger = logging.getLogger(__name__)


class ContactService(BaseService[Contact]):
    """
    Service for managing contacts.

    All reads are scoped to the current user via `get_for_user()`.
    The Contact model uses `owner` as the ownership field.

    Usage:
        service = ContactService(user=request.user)
        result = service.list_contacts(search_query="john")
        contact = service.create_contact(form_data={...})
    """

    model = Contact

    # ── List / Search ────────────────────────────────────────────────────

    def _base_queryset(self) -> models.QuerySet[Contact]:
        """
        Base queryset scoped to the current user.

        Uses get_for_user() which filters by the `owner` field,
        ensuring users can only see their own contacts.
        """
        qs = self.get_for_user()
        # Apply active filter (excludes soft-deleted)
        if hasattr(qs, "active"):
            return qs
        return qs.filter(is_deleted=False)

    def list_contacts(
        self,
        search_query: Optional[str] = None,
        tag_slug: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        """
        List contacts for the current user with optional filtering and pagination.

        Returns a dict with 'items' (serialized contacts), 'filters', and 'pagination'.
        """
        qs = self._base_queryset()

        if search_query:
            from django.db.models import Q

            q = Q()
            for field in ("name", "email", "phone", "company"):
                q |= Q(**{f"{field}__icontains": search_query})
            qs = qs.filter(q)

        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        qs = qs.order_by("-created_at")
        total = qs.count()
        total_pages = (total + per_page - 1) // per_page if total else 1
        offset = (page - 1) * per_page
        contacts = qs[offset : offset + per_page]

        return {
            "items": [c.to_dict() for c in contacts],
            "filters": {
                "q": search_query or "",
                "tag": tag_slug,
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": total_pages,
            },
        }

    def search_contacts(self, query: str) -> models.QuerySet[Contact]:
        """
        Search contacts owned by the current user.

        Uses icontains across name, email, phone, company.
        """
        from django.db.models import Q

        qs = self._base_queryset()
        q = Q()
        for field in ("name", "email", "phone", "company"):
            q |= Q(**{f"{field}__icontains": query})
        return qs.filter(q)

    # ── Single Record ────────────────────────────────────────────────────

    def get_contact(self, public_id: str) -> Contact:
        """
        Get a contact by public_id, scoped to the current user.

        Raises Http404 if not found or not owned by the current user.
        """
        return self.get_for_user_by_public_id_or_404(public_id)

    # ── Create / Update / Delete ─────────────────────────────────────────

    @transaction.atomic
    def create_contact(
        self, form_data: dict[str, Any]
    ) -> tuple[Optional[Contact], Optional[dict]]:
        """
        Create a new contact using ContactForm for validation.

        Args:
            form_data: Dict of form field values (from request.data via InertiaJsonParserMiddleware).

        Returns:
            Tuple of (contact, None) on success, or (None, errors_dict) on failure.
        """
        form = ContactForm(form_data)

        if not form.is_valid():
            return None, form.errors

        contact = form.save(commit=False)
        contact.created_by = self.user
        contact.owner = self.user
        contact.save()
        form.save_m2m()  # Save tags M2M relationship

        logger.info(
            "Created contact %s (%s) by user=%s",
            contact.name,
            contact.public_id,
            self.user,
        )
        return contact, None

    @transaction.atomic
    def update_contact(
        self, public_id: str, form_data: dict[str, Any]
    ) -> tuple[Optional[Contact], Optional[dict]]:
        """
        Update an existing contact using ContactForm for validation.

        Verifies ownership before updating.

        Args:
            public_id: The public_id of the contact to update.
            form_data: Dict of form field values.

        Returns:
            Tuple of (contact, None) on success, or (contact, errors_dict) on failure.
            The contact is always returned so the view can re-render with current data.
        """
        contact = self.get_for_user_by_public_id_or_404(public_id)
        form = ContactForm(form_data, instance=contact)

        if not form.is_valid():
            return contact, form.errors

        contact = form.save()

        logger.info(
            "Updated contact %s (%s) by user=%s",
            contact.name,
            contact.public_id,
            self.user,
        )
        return contact, None

    @transaction.atomic
    def delete_contact(self, public_id: str) -> str:
        """
        Soft-delete a contact by public_id.

        Verifies ownership before deleting.

        Args:
            public_id: The public_id of the contact to delete.

        Returns:
            The name of the deleted contact (for flash messages).
        """
        contact = self.get_for_user_by_public_id_or_404(public_id)
        name = contact.name
        self.delete(contact)

        logger.info(
            "Deleted contact %s (%s) by user=%s",
            name,
            public_id,
            self.user,
        )
        return name
