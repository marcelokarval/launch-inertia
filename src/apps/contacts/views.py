"""
Identity views using Inertia.js.

Thin views that delegate business logic to IdentityService.
Identity is the primary entity — the CRM Contact has been eliminated.

Security:
- All views require authentication (@login_required)
- Identity doesn't have per-user ownership (it's the person's record, not the operator's)
- Soft-delete is available for cleanup
"""

import logging
from typing import Any

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Subquery, OuterRef
from django.http import Http404, JsonResponse
from django.shortcuts import redirect

from core.inertia import inertia_render, flash_success

from apps.contacts.identity.models import Identity
from apps.contacts.identity.services import IdentityService

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """List all active identities with filtering and pagination."""
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    per_page = 25
    search_query = request.GET.get("q", "") or None
    tag_slug = request.GET.get("tag") or None

    from apps.contacts.email.models import ContactEmail

    qs = (
        Identity.objects.filter(is_deleted=False, status=Identity.ACTIVE)
        .annotate(
            _email_count=Count("email_contacts", distinct=True),
            _phone_count=Count("phone_contacts", distinct=True),
            _fingerprint_count=Count("fingerprints", distinct=True),
            _primary_email=Subquery(
                ContactEmail.objects.filter(
                    identity_id=OuterRef("pk"),
                ).values("value")[:1]
            ),
        )
        .prefetch_related("tags")
    )

    if search_query:
        q = Q()
        q |= Q(display_name__icontains=search_query)
        q |= Q(email_contacts__value__icontains=search_query)
        q |= Q(phone_contacts__value__icontains=search_query)
        qs = qs.filter(q).distinct()

    if tag_slug:
        qs = qs.filter(tags__slug=tag_slug)

    qs = qs.order_by("-created_at")
    total = qs.count()
    total_pages = (total + per_page - 1) // per_page if total else 1
    offset = (page - 1) * per_page
    identities = qs[offset : offset + per_page]

    return inertia_render(
        request,
        "Identity/Index",
        {
            "identities": [i.to_list_dict() for i in identities],
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
        },
    )


@login_required
def show(request, public_id):
    """Show identity details with full channels, attributions, and timeline.

    Passes:
    - identity: full identity with emails, phones, fingerprints
    - attributions: marketing attribution records
    - timeline: fingerprint events ordered by timestamp
    """
    try:
        identity = Identity.objects.get(public_id=public_id, is_deleted=False)
    except Identity.DoesNotExist:
        raise Http404("Identity not found")

    identity_data = identity.to_dict(include_contacts=True)

    identity_data["attributions"] = [
        a.to_dict() for a in identity.attributions.all()[:50]
    ]
    identity_data["timeline"] = identity.get_timeline()

    # Extract intent hints from form_intent CaptureEvents (P3.3)
    # Useful when identity has no contacts yet — shows partial data
    from core.tracking.models import CaptureEvent

    intent_events = CaptureEvent.objects.filter(
        identity=identity,
        event_type=CaptureEvent.EventType.FORM_INTENT,
    ).order_by("-created_at")[:10]

    intent_hints: dict[str, set[str]] = {
        "email_domains": set(),
        "phone_prefixes": set(),
    }
    for evt in intent_events:
        extra = evt.extra_data or {}
        if domain := extra.get("email_domain"):
            intent_hints["email_domains"].add(str(domain))
        if prefix := extra.get("phone_prefix"):
            intent_hints["phone_prefixes"].add(str(prefix))

    identity_data["intent_hints"] = {
        "email_domains": sorted(intent_hints["email_domains"]),
        "phone_prefixes": sorted(intent_hints["phone_prefixes"]),
    }

    # Overview stats for P3.1 Overview tab
    all_events = CaptureEvent.objects.filter(identity=identity)
    identity_data["overview_stats"] = {
        "page_views": all_events.filter(
            event_type=CaptureEvent.EventType.PAGE_VIEW,
        ).count(),
        "form_intents": all_events.filter(
            event_type=CaptureEvent.EventType.FORM_INTENT,
        ).count(),
        "form_submissions": all_events.filter(
            event_type=CaptureEvent.EventType.FORM_SUCCESS,
        ).count(),
        "total_events": all_events.count(),
    }

    return inertia_render(
        request,
        "Identity/Show",
        {
            "identity": identity_data,
        },
    )


@login_required
def create(request):
    """Import a new identity by providing email and/or phone.

    Uses ResolutionService to find or create the identity, avoiding duplicates.
    """
    if request.method == "POST":
        from apps.contacts.identity.services import ResolutionService

        email = (request.data.get("email") or "").strip().lower()
        phone = (request.data.get("phone") or "").strip()
        display_name = (request.data.get("display_name") or "").strip()

        errors: dict[str, Any] = {}
        if not email and not phone:
            errors["email"] = "At least email or phone is required."
            errors["phone"] = "At least email or phone is required."

        if errors:
            return inertia_render(
                request,
                "Identity/Create",
                {"errors": errors},
            )

        # Build contact_data for resolution
        contact_data = {}
        if email:
            contact_data["email"] = email
        if phone:
            contact_data["phone"] = phone

        try:
            result = ResolutionService.resolve_identity_from_real_data(
                fingerprint_data={},
                contact_data=contact_data if contact_data else None,
            )
            identity = Identity.objects.get(pk=result["identity_id"])

            # Update display_name if provided and not already set
            if display_name and not identity.display_name:
                identity.display_name = display_name
                identity.save(update_fields=["display_name", "updated_at"])

            action = "imported" if not result.get("is_new") else "created"
            flash_success(
                request,
                f"Identity {identity.display_name or identity.public_id} {action} successfully!",
            )
            return redirect("identities:show", public_id=identity.public_id)

        except Exception as e:
            logger.exception("Failed to create/resolve identity: %s", e)
            return inertia_render(
                request,
                "Identity/Create",
                {"errors": {"__all__": str(e)}},
            )

    return inertia_render(request, "Identity/Create")


@login_required
def edit(request, public_id):
    """Edit identity operator fields: display_name, notes, tags."""
    try:
        identity = Identity.objects.get(public_id=public_id, is_deleted=False)
    except Identity.DoesNotExist:
        raise Http404("Identity not found")

    if request.method == "POST":
        display_name = (request.data.get("display_name") or "").strip()
        operator_notes = (request.data.get("operator_notes") or "").strip()

        identity.display_name = display_name
        identity.operator_notes = operator_notes
        identity.save(update_fields=["display_name", "operator_notes", "updated_at"])

        # Handle tags (tag IDs sent from frontend)
        tag_ids = request.data.get("tag_ids")
        if tag_ids is not None:
            from apps.contacts.models import Tag

            if isinstance(tag_ids, list):
                tags = Tag.objects.filter(public_id__in=tag_ids, is_deleted=False)
                identity.tags.set(tags)
            elif tag_ids == "" or tag_ids == []:
                identity.tags.clear()

        flash_success(
            request,
            f"Identity {identity.display_name or identity.public_id} updated!",
        )
        return redirect("identities:show", public_id=identity.public_id)

    identity_data = identity.to_dict()

    return inertia_render(
        request,
        "Identity/Edit",
        {
            "identity": identity_data,
        },
    )


@login_required
def delete(request, public_id):
    """Soft-delete an identity."""
    try:
        identity = Identity.objects.get(public_id=public_id, is_deleted=False)
    except Identity.DoesNotExist:
        raise Http404("Identity not found")

    if request.method == "POST":
        display = identity.display_name or identity.public_id
        identity.delete()
        flash_success(request, f"Identity {display} deleted.")
        return redirect("identities:index")

    identity_data = identity.to_dict()

    return inertia_render(
        request,
        "Identity/Delete",
        {
            "identity": identity_data,
        },
    )


# ── API Endpoints (JSON, not Inertia) ────────────────────────────────


@login_required
def expand(request, public_id):
    """
    Expand-on-demand endpoint for Identity detail view.

    Returns full channel details, attributions, lifecycle cache, and
    launch participation data (placeholder until Phase 4).

    This is a JSON endpoint — used by the frontend for lazy loading
    when the operator clicks "Ver detalhes" on an Identity card.

    URL: GET /identities/<public_id>/expand/
    """
    try:
        identity = Identity.objects.get(public_id=public_id, is_deleted=False)
    except Identity.DoesNotExist:
        return JsonResponse(
            {"error": "Identity not found"},
            status=404,
        )

    from apps.contacts.identity.services.lifecycle_service import LifecycleService

    data = LifecycleService.get_expanded_data(identity)

    return JsonResponse(data, status=200)


@login_required
def recalculate_lifecycle(request, public_id):
    """
    Trigger lifecycle_global recalculation for a specific Identity.

    POST-only endpoint for manual cache refresh from the frontend.

    URL: POST /identities/<public_id>/recalculate/
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    try:
        identity = Identity.objects.get(public_id=public_id, is_deleted=False)
    except Identity.DoesNotExist:
        return JsonResponse(
            {"error": "Identity not found"},
            status=404,
        )

    from apps.contacts.identity.services.lifecycle_service import LifecycleService

    lifecycle = LifecycleService.recalculate(identity)

    return JsonResponse(
        {
            "status": "success",
            "lifecycle": lifecycle,
        },
        status=200,
    )
