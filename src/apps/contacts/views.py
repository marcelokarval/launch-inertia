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
    """Identity Hub — tabbed view of the identity ecosystem.

    Tabs: overview | people | emails | phones | devices
    Each tab loads only its own data. Common counts are always included.
    """
    tab = request.GET.get("tab", "overview")
    valid_tabs = {"overview", "people", "emails", "phones", "devices"}
    if tab not in valid_tabs:
        tab = "overview"

    from apps.contacts.email.models import ContactEmail
    from apps.contacts.phone.models import ContactPhone
    from apps.contacts.fingerprint.models import FingerprintIdentity
    from core.tracking.models import CaptureEvent, DeviceProfile

    active_identities = Identity.objects.filter(
        is_deleted=False,
        status=Identity.ACTIVE,
    )

    # ── Common counts (always sent, used for tab badges) ──
    counts = {
        "people": active_identities.count(),
        "emails": ContactEmail.objects.filter(
            identity__in=active_identities,
        ).count(),
        "phones": ContactPhone.objects.filter(
            identity__in=active_identities,
        ).count(),
        "devices": DeviceProfile.objects.filter(
            tracking_events__identity__in=active_identities,
        )
        .distinct()
        .count(),
    }

    props: dict[str, Any] = {"tab": tab, "counts": counts}

    # ── Tab-specific data ──

    if tab == "overview":
        props.update(_build_overview_data(active_identities, CaptureEvent))

    elif tab == "people":
        props.update(
            _build_people_data(
                request,
                active_identities,
                ContactEmail,
                ContactPhone,
                CaptureEvent,
            )
        )

    elif tab == "emails":
        props.update(
            _build_emails_data(request, active_identities, ContactEmail, CaptureEvent)
        )

    elif tab == "phones":
        props.update(
            _build_phones_data(request, active_identities, ContactPhone, CaptureEvent)
        )

    elif tab == "devices":
        props.update(
            _build_devices_data(active_identities, DeviceProfile, FingerprintIdentity)
        )

    return inertia_render(request, "Identity/Index", props)


def _build_overview_data(active_identities, CaptureEvent) -> dict[str, Any]:  # type: ignore[type-arg]
    """Build data for the Overview tab."""
    from apps.contacts.models import Tag

    all_events = CaptureEvent.objects.filter(identity__in=active_identities)

    # Recent events (last 15)
    recent_events = []
    for evt in all_events.select_related("identity").order_by("-created_at")[:15]:
        recent_events.append(
            {
                "id": evt.public_id,
                "event_type": evt.event_type,
                "page_path": evt.page_path,
                "created_at": evt.created_at.isoformat() if evt.created_at else None,
                "identity_id": evt.identity.public_id if evt.identity else None,
                "identity_name": evt.identity.display_name if evt.identity else None,
            }
        )

    # Attribution sources (top 10)
    from apps.contacts.identity.models import Attribution

    source_counts = (
        Attribution.objects.filter(identity__in=active_identities)
        .values("utm_source")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    attribution_sources = [
        {"source": s["utm_source"] or "(direct)", "count": s["count"]}
        for s in source_counts
    ]

    # Domain + prefix hints (aggregated from form_intent events)
    domain_hints: dict[str, list[str]] = {}
    prefix_hints: dict[str, list[str]] = {}
    intent_events = (
        all_events.filter(
            event_type=CaptureEvent.EventType.FORM_INTENT,
        )
        .select_related("identity")
        .order_by("-created_at")[:50]
    )

    for evt in intent_events:
        extra = evt.extra_data or {}
        idt_id = evt.identity.public_id if evt.identity else "unknown"
        if d := extra.get("email_domain"):
            domain_hints.setdefault(str(d), [])
            if idt_id not in domain_hints[str(d)]:
                domain_hints[str(d)].append(idt_id)
        if p := extra.get("phone_prefix"):
            prefix_hints.setdefault(str(p), [])
            if idt_id not in prefix_hints[str(p)]:
                prefix_hints[str(p)].append(idt_id)

    # Tags with identity count
    tags = [
        {
            "id": t.public_id,
            "name": t.name,
            "slug": t.slug,
            "color": t.color,
            "identity_count": t.identities.filter(
                is_deleted=False,
                status="active",
            ).count(),
        }
        for t in Tag.objects.filter(is_deleted=False)
    ]

    # Anonymous vs identified counts
    identified_count = (
        active_identities.filter(
            Q(email_contacts__isnull=False) | Q(phone_contacts__isnull=False),
        )
        .distinct()
        .count()
    )

    return {
        "overview": {
            "total_events": all_events.count(),
            "total_page_views": all_events.filter(
                event_type=CaptureEvent.EventType.PAGE_VIEW,
            ).count(),
            "total_form_intents": all_events.filter(
                event_type=CaptureEvent.EventType.FORM_INTENT,
            ).count(),
            "identified_count": identified_count,
            "anonymous_count": active_identities.count() - identified_count,
            "recent_events": recent_events,
            "attribution_sources": attribution_sources,
            "domain_hints": [
                {"domain": d, "identities": ids}
                for d, ids in sorted(domain_hints.items())
            ],
            "prefix_hints": [
                {"prefix": p, "identities": ids}
                for p, ids in sorted(prefix_hints.items())
            ],
            "tags": tags,
        },
    }


def _build_people_data(
    request, active_identities, ContactEmail, ContactPhone, CaptureEvent
) -> dict[str, Any]:  # type: ignore[type-arg]
    """Build data for the People tab (previous Index logic)."""
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    per_page = 25
    search_query = request.GET.get("q", "") or None
    tag_slug = request.GET.get("tag") or None

    qs = active_identities.annotate(
        _email_count=Count("email_contacts", distinct=True),
        _phone_count=Count("phone_contacts", distinct=True),
        _fingerprint_count=Count("fingerprints", distinct=True),
        _primary_email=Subquery(
            ContactEmail.objects.filter(
                identity_id=OuterRef("pk"),
            ).values("value")[:1]
        ),
        _primary_phone=Subquery(
            ContactPhone.objects.filter(
                identity_id=OuterRef("pk"),
            ).values("value")[:1]
        ),
        _page_view_count=Count(
            "tracking_events",
            filter=Q(tracking_events__event_type=CaptureEvent.EventType.PAGE_VIEW),
        ),
        _total_event_count=Count("tracking_events"),
    ).prefetch_related("tags")

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

    return {
        "identities": [i.to_list_dict() for i in identities],
        "filters": {"q": search_query or "", "tag": tag_slug},
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages,
        },
    }


def _build_emails_data(
    request, active_identities, ContactEmail, CaptureEvent
) -> dict[str, Any]:  # type: ignore[type-arg]
    """Build data for the Emails tab."""
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    per_page = 25
    search_query = request.GET.get("q", "") or None

    qs = (
        ContactEmail.objects.filter(
            identity__in=active_identities,
        )
        .select_related("identity")
        .order_by("-created_at")
    )

    if search_query:
        qs = qs.filter(
            Q(value__icontains=search_query) | Q(domain__icontains=search_query)
        )

    total = qs.count()
    total_pages = (total + per_page - 1) // per_page if total else 1
    offset = (page - 1) * per_page
    emails = qs[offset : offset + per_page]

    email_list = []
    for e in emails:
        email_list.append(
            {
                "id": e.public_id,
                "value": e.value,
                "domain": e.domain,
                "lifecycle_status": e.lifecycle_status,
                "is_verified": e.is_verified,
                "quality_score": e.quality_score,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
                "identity_id": e.identity.public_id if e.identity else None,
                "identity_name": e.identity.display_name if e.identity else None,
            }
        )

    # Domain hints from form_intent (for empty state)
    domain_hints = _get_domain_hints(active_identities, CaptureEvent)

    return {
        "emails": email_list,
        "domain_hints": domain_hints,
        "filters": {"q": search_query or ""},
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages,
        },
    }


def _build_phones_data(
    request, active_identities, ContactPhone, CaptureEvent
) -> dict[str, Any]:  # type: ignore[type-arg]
    """Build data for the Phones tab."""
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    per_page = 25
    search_query = request.GET.get("q", "") or None

    qs = (
        ContactPhone.objects.filter(
            identity__in=active_identities,
        )
        .select_related("identity")
        .order_by("-created_at")
    )

    if search_query:
        qs = qs.filter(value__icontains=search_query)

    total = qs.count()
    total_pages = (total + per_page - 1) // per_page if total else 1
    offset = (page - 1) * per_page
    phones = qs[offset : offset + per_page]

    phone_list = []
    for p in phones:
        phone_list.append(
            {
                "id": p.public_id,
                "value": p.value,
                "country_code": p.country_code,
                "phone_type": p.phone_type,
                "display_value": p.format_for_display(),
                "is_verified": p.is_verified,
                "is_whatsapp": p.is_whatsapp,
                "is_sms_capable": p.is_sms_capable,
                "first_seen": p.first_seen.isoformat() if p.first_seen else None,
                "last_seen": p.last_seen.isoformat() if p.last_seen else None,
                "identity_id": p.identity.public_id if p.identity else None,
                "identity_name": p.identity.display_name if p.identity else None,
            }
        )

    # Prefix hints from form_intent (for empty state)
    prefix_hints = _get_prefix_hints(active_identities, CaptureEvent)

    return {
        "phones": phone_list,
        "prefix_hints": prefix_hints,
        "filters": {"q": search_query or ""},
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": total_pages,
        },
    }


def _build_devices_data(
    active_identities, DeviceProfile, FingerprintIdentity
) -> dict[str, Any]:  # type: ignore[type-arg]
    """Build data for the Devices tab."""
    # Device profiles that have events linked to active identities
    device_qs = (
        DeviceProfile.objects.filter(
            tracking_events__identity__in=active_identities,
        )
        .distinct()
        .annotate(
            _event_count=Count("tracking_events"),
        )
        .order_by("-_event_count")[:50]
    )

    device_list = []
    for d in device_qs:
        # Find which identities used this device
        identity_ids = list(
            d.tracking_events.filter(
                identity__in=active_identities,
            )
            .values_list("identity__public_id", flat=True)
            .distinct()[:10]
        )
        device_list.append(
            {
                "id": d.public_id,
                "browser_family": d.browser_family,
                "browser_version": d.browser_version,
                "os_family": d.os_family,
                "os_version": d.os_version,
                "device_type": d.device_type,
                "device_brand": d.device_brand,
                "is_bot": d.is_bot,
                "event_count": getattr(d, "_event_count", 0),
                "identity_ids": identity_ids,
            }
        )

    # FingerprintJS identities (separate from device profiles)
    fp_list = []
    for fp in (
        FingerprintIdentity.objects.filter(
            identity__in=active_identities,
        )
        .select_related("identity")
        .order_by("-last_seen")[:50]
    ):
        fp_list.append(
            {
                "id": fp.public_id,
                "hash": fp.hash[:12] + "...",
                "confidence_score": fp.confidence_score,
                "browser": fp.browser,
                "os": fp.os,
                "device_type": fp.device_type,
                "is_master": fp.is_master,
                "first_seen": fp.first_seen.isoformat() if fp.first_seen else None,
                "last_seen": fp.last_seen.isoformat() if fp.last_seen else None,
                "identity_id": fp.identity.public_id if fp.identity else None,
                "identity_name": fp.identity.display_name if fp.identity else None,
            }
        )

    return {
        "devices": device_list,
        "fingerprints": fp_list,
    }


def _get_domain_hints(active_identities, CaptureEvent) -> list[dict[str, Any]]:  # type: ignore[type-arg]
    """Get email domain hints from form_intent events."""
    hints: dict[str, list[str]] = {}
    for evt in (
        CaptureEvent.objects.filter(
            identity__in=active_identities,
            event_type=CaptureEvent.EventType.FORM_INTENT,
        )
        .select_related("identity")
        .order_by("-created_at")[:50]
    ):
        extra = evt.extra_data or {}
        if d := extra.get("email_domain"):
            idt_id = evt.identity.public_id if evt.identity else "unknown"
            hints.setdefault(str(d), [])
            if idt_id not in hints[str(d)]:
                hints[str(d)].append(idt_id)
    return [{"domain": d, "identities": ids} for d, ids in sorted(hints.items())]


def _get_prefix_hints(active_identities, CaptureEvent) -> list[dict[str, Any]]:  # type: ignore[type-arg]
    """Get phone prefix hints from form_intent events."""
    hints: dict[str, list[str]] = {}
    for evt in (
        CaptureEvent.objects.filter(
            identity__in=active_identities,
            event_type=CaptureEvent.EventType.FORM_INTENT,
        )
        .select_related("identity")
        .order_by("-created_at")[:50]
    ):
        extra = evt.extra_data or {}
        if p := extra.get("phone_prefix"):
            idt_id = evt.identity.public_id if evt.identity else "unknown"
            hints.setdefault(str(p), [])
            if idt_id not in hints[str(p)]:
                hints[str(p)].append(idt_id)
    return [{"prefix": p, "identities": ids} for p, ids in sorted(hints.items())]


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

    # Overview stats for P3.1 Overview tab + P4.2 session history
    from django.db.models.functions import TruncDate

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
        # P4.2 — Session history (computed from CaptureEvents)
        "visit_sessions": all_events.values("capture_token").distinct().count(),
        "unique_pages": all_events.values("page_path").distinct().count(),
        "days_active": (
            all_events.annotate(day=TruncDate("created_at"))
            .values("day")
            .distinct()
            .count()
        ),
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
