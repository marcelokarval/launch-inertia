"""
Notifications views using Inertia.js.

Thin view layer that delegates all business logic to NotificationService.

Security:
- All views require authentication (@login_required)
- mark_read uses @require_ownership for IDOR protection (defense-in-depth)
- list_notifications is scoped by user inside NotificationService
- Page parameter has safe int conversion
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from core.inertia import inertia_render, flash_success
from core.security.decorators import require_ownership
from .models import Notification
from .services import NotificationService


@login_required
def index(request):
    """List all notifications for the current user."""
    service = NotificationService(user=request.user)

    status_filter = request.GET.get("status", "all")

    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    data = service.list_notifications(
        user=request.user,
        status_filter=status_filter,
        page=page,
    )

    return inertia_render(
        request,
        "Notifications/Index",
        {
            "notifications": data["items"],
            "filter": status_filter,
            "pagination": data["pagination"],
            "unread_count": data["unread_count"],
        },
    )


@login_required
@require_POST
@require_ownership(Notification, owner_field="recipient")
def mark_read(request, public_id):
    """Mark a single notification as read. Ownership verified by @require_ownership."""
    service = NotificationService(user=request.user)
    service.mark_as_read(user=request.user, public_id=public_id)

    if request.headers.get("X-Inertia"):
        return redirect("notifications:index")

    return JsonResponse({"success": True})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    service = NotificationService(user=request.user)
    service.mark_all_as_read(user=request.user)

    flash_success(request, "All notifications marked as read.")
    return redirect("notifications:index")
