"""
Inertia.js helper functions for Django views.
"""
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from inertia import render as inertia_base_render


def inertia_render(
    request: HttpRequest,
    component: str,
    props: dict[str, Any] | None = None,
    *,
    app: str = "dashboard",
) -> HttpResponse:
    """
    Render an Inertia response with multi-frontend layout support.

    Args:
        request: The HTTP request
        component: The React component name (e.g., "Dashboard/Index")
        props: Props to pass to the component
        app: Which frontend app to render with ("dashboard" or "landing").
             Determines the base template used.

    Returns:
        HttpResponse: Inertia response

    Usage:
        # Dashboard (default — uses dashboard.html template)
        def index(request):
            return inertia_render(request, "Dashboard/Index", {
                "stats": get_dashboard_stats(),
            })

        # Landing (uses landing.html template)
        def capture(request):
            return inertia_render(request, "Capture/Index", {
                "campaign": "wh-rc-v1",
            }, app="landing")
    """
    layouts = getattr(settings, "INERTIA_LAYOUTS", {})
    template_name = layouts.get(app, settings.INERTIA_LAYOUT)

    return inertia_base_render(
        request,
        component,
        props=props or {},
        template_name=template_name,
    )


def flash(request: HttpRequest, message: str, level: str = "info") -> None:
    """
    Add a flash message that will be shown on the next page.

    Args:
        request: The HTTP request
        message: The message to display
        level: Message level (success, error, warning, info)

    Usage:
        flash(request, "Contact created successfully!", "success")
        return redirect("contacts:index")
    """
    level_map = {
        "success": messages.SUCCESS,
        "error": messages.ERROR,
        "warning": messages.WARNING,
        "info": messages.INFO,
    }
    messages.add_message(request, level_map.get(level, messages.INFO), message)


def flash_success(request: HttpRequest, message: str) -> None:
    """Add a success flash message."""
    flash(request, message, "success")


def flash_error(request: HttpRequest, message: str) -> None:
    """Add an error flash message."""
    flash(request, message, "error")


def flash_warning(request: HttpRequest, message: str) -> None:
    """Add a warning flash message."""
    flash(request, message, "warning")


def flash_info(request: HttpRequest, message: str) -> None:
    """Add an info flash message."""
    flash(request, message, "info")
