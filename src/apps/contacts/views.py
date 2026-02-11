"""
Contacts views using Inertia.js.

Thin views that delegate business logic to ContactService.

Security:
- All views require authentication (@login_required)
- show/edit/delete use @require_ownership for IDOR protection
- list_contacts is scoped by user inside ContactService
- create sets owner=request.user inside ContactService
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from core.inertia import inertia_render, flash_success
from core.security.decorators import require_ownership
from .models import Contact
from .services import ContactService


@login_required
def index(request):
    """List all contacts for the current user with filtering and pagination."""
    service = ContactService(user=request.user)

    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    result = service.list_contacts(
        search_query=request.GET.get("q", "") or None,
        tag_slug=request.GET.get("tag") or None,
        page=page,
    )

    return inertia_render(
        request,
        "Contacts/Index",
        {
            "contacts": result["items"],
            "filters": result["filters"],
            "pagination": result["pagination"],
        },
    )


@login_required
@require_ownership(Contact, owner_field="owner")
def show(request, public_id):
    """Show contact details with full identity resolution data.

    Passes:
    - contact: CRM contact with details
    - identity: resolved identity with emails, phones, fingerprints (if linked)
    - attributions: marketing attribution records
    - timeline: fingerprint events ordered by timestamp
    """
    contact = request.verified_object
    contact_data = contact.to_dict(include_details=True)

    identity_data = None
    attributions_data = []
    timeline_data = []

    if contact.identity:
        identity = contact.identity
        identity_data = identity.to_dict(include_contacts=True)
        attributions_data = [a.to_dict() for a in identity.attributions.all()[:50]]
        timeline_data = [e.to_dict() for e in identity.get_timeline()[:100]]

    contact_data["identity"] = identity_data
    contact_data["attributions"] = attributions_data
    contact_data["timeline"] = timeline_data

    return inertia_render(
        request,
        "Contacts/Show",
        {
            "contact": contact_data,
        },
    )


@login_required
def create(request):
    """Create new contact. Owner is set to the current user by ContactService."""
    service = ContactService(user=request.user)

    if request.method == "POST":
        contact, errors = service.create_contact(request.data)

        if errors:
            return inertia_render(
                request,
                "Contacts/Create",
                {
                    "errors": errors,
                },
            )

        flash_success(request, f"Contact {contact.name} created successfully!")
        return redirect("contacts:show", public_id=contact.public_id)

    return inertia_render(request, "Contacts/Create")


@login_required
@require_ownership(Contact, owner_field="owner")
def edit(request, public_id):
    """Edit contact. Ownership verified by @require_ownership."""
    service = ContactService(user=request.user)

    if request.method == "POST":
        contact, errors = service.update_contact(public_id, request.data)

        if errors:
            return inertia_render(
                request,
                "Contacts/Edit",
                {
                    "contact": contact.to_dict(),
                    "errors": errors,
                },
            )

        flash_success(request, f"Contact {contact.name} updated successfully!")
        return redirect("contacts:show", public_id=contact.public_id)

    contact = request.verified_object
    return inertia_render(
        request,
        "Contacts/Edit",
        {
            "contact": contact.to_dict(),
        },
    )


@login_required
@require_ownership(Contact, owner_field="owner")
def delete(request, public_id):
    """Delete contact (soft delete). Ownership verified by @require_ownership."""
    service = ContactService(user=request.user)

    if request.method == "POST":
        name = service.delete_contact(public_id)
        flash_success(request, f"Contact {name} deleted.")
        return redirect("contacts:index")

    contact = request.verified_object
    return inertia_render(
        request,
        "Contacts/Delete",
        {
            "contact": contact.to_dict(),
        },
    )
