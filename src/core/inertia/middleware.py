"""
Inertia.js middleware collection.

Includes:
- InertiaJsonParserMiddleware: Parses JSON request body into request.data
- InertiaShareMiddleware: Shares common data with all Inertia pages
- SetupStatusMiddleware: Redirects incomplete users to onboarding
- DelinquentMiddleware: Restricts access for delinquent billing users
"""

import json
import logging
from typing import Any, Callable

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import redirect
from inertia import share

logger = logging.getLogger(__name__)


class InertiaJsonParserMiddleware:
    """
    Middleware that parses JSON request bodies from Inertia.js into request.data.

    Inertia.js sends POST/PUT/PATCH/DELETE requests with Content-Type: application/json
    by default. Django's request.POST only works with form-encoded or multipart data,
    so JSON bodies are invisible to request.POST.

    This middleware solves that by providing request.data:
    - If the request has a JSON body -> request.data = parsed JSON dict
    - If the request has form-encoded body -> request.data = request.POST (QueryDict)
    - If the request is GET or has no body -> request.data = empty QueryDict

    Usage in views (MANDATORY — all views must use request.data):
        name = request.data.get("name", "")

    Note: This does NOT modify request.POST. It adds a separate request.data attribute.
    Do NOT use request.POST in views — always use request.data for consistency.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.data = self._parse_request_data(request)  # type: ignore[attr-defined]
        return self.get_response(request)

    def _parse_request_data(self, request: HttpRequest) -> QueryDict | dict[str, Any]:
        """
        Parse request body based on content type.

        Returns QueryDict for form-encoded data (preserving Django conventions)
        or a plain dict for JSON data.
        """
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return QueryDict()

        content_type = getattr(request, "content_type", "")

        if "application/json" in content_type:
            try:
                body = request.body
                if body:
                    return json.loads(body)
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "InertiaJsonParserMiddleware: Failed to parse JSON body for %s %s",
                    request.method,
                    request.path,
                )
            return {}

        # For form-encoded / multipart, fall back to request.POST
        return request.POST


class InertiaShareMiddleware:
    """
    Middleware that shares common data with all Inertia pages.

    Shared data includes:
    - auth: Current user information
    - flash: Flash messages from Django messages framework
    - app: Application configuration
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Share data with Inertia (evaluated lazily at render time)
        share(
            request,
            # Authentication data
            auth=lambda: self._get_auth_data(request),
            # Flash messages
            flash=lambda: self._get_flash_messages(request),
            # App configuration
            app=lambda: self._get_app_config(request),
            # Locale data for i18n
            locale=lambda: self._get_locale_data(request),
        )

        return self.get_response(request)

    def _get_auth_data(self, request: HttpRequest) -> dict:
        """Get authenticated user data."""
        if not request.user.is_authenticated:
            return {"user": None}

        user = request.user
        return {
            "user": {
                "id": user.public_id if hasattr(user, "public_id") else user.id,
                "email": user.email,
                "name": self._get_user_name(user),
                "avatar": self._get_user_avatar(user),
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        }

    def _get_user_name(self, user) -> str:
        """Get user's display name."""
        if hasattr(user, "get_full_name"):
            full_name = user.get_full_name()
            if full_name:
                return full_name
        if hasattr(user, "first_name") and user.first_name:
            return user.first_name
        return user.email.split("@")[0]

    def _get_user_avatar(self, user) -> str | None:
        """Get user's avatar URL."""
        if hasattr(user, "profile") and hasattr(user.profile, "avatar"):
            avatar = user.profile.avatar
            if avatar:
                return avatar.url
        return None

    def _get_flash_messages(self, request: HttpRequest) -> dict:
        """Get flash messages from Django messages framework."""
        storage = messages.get_messages(request)
        flash_messages = {
            "success": None,
            "error": None,
            "warning": None,
            "info": None,
        }

        for message in storage:
            # Map Django message tags to our flash types
            tag = message.tags
            if "success" in tag:
                flash_messages["success"] = str(message)
            elif "error" in tag or "danger" in tag:
                flash_messages["error"] = str(message)
            elif "warning" in tag:
                flash_messages["warning"] = str(message)
            else:
                flash_messages["info"] = str(message)

        return flash_messages

    def _get_app_config(self, request: HttpRequest) -> dict:
        """Get application configuration for frontend."""
        return {
            "name": getattr(settings, "APP_NAME", "Launch"),
            "debug": settings.DEBUG,
            "timezone": getattr(settings, "TIME_ZONE", "America/Sao_Paulo"),
            "csrf_token": request.META.get("CSRF_COOKIE", ""),
        }

    def _get_locale_data(self, request: HttpRequest) -> dict:
        """Get locale information for frontend i18n."""
        return {
            "language": getattr(request, "LANGUAGE_CODE", "pt"),
        }


class _DashboardOnlyMiddleware:
    """Base class for middleware that only applies to dashboard routes.

    Landing pages (public routes) are never subject to dashboard guards
    like onboarding or billing checks. This base class provides the
    path-matching logic shared by SetupStatusMiddleware and
    DelinquentMiddleware.

    A route is considered a dashboard route if it starts with one of
    DASHBOARD_PREFIXES. All other routes are skipped automatically.
    """

    # Only these prefixes trigger guard checks.
    # Landing pages, admin, static, etc. are always allowed through.
    DASHBOARD_PREFIXES = (
        "/app/",
        # Temporary: existing routes before /app/ migration
        "/dashboard/",
        "/identities/",
        "/billing/",
        "/notifications/",
        "/settings/",
        "/delinquent/",
    )

    def _is_dashboard_route(self, path: str) -> bool:
        """Return True if this path belongs to the dashboard frontend."""
        return any(path.startswith(prefix) for prefix in self.DASHBOARD_PREFIXES)


class SetupStatusMiddleware(_DashboardOnlyMiddleware):
    """
    Middleware that redirects users with incomplete onboarding to the
    appropriate onboarding step.

    Only applies to dashboard routes (authenticated area). Landing pages
    and other public routes are never intercepted.

    Exempt paths within dashboard scope:
    - /auth/, /onboarding/, /api/, /accounts/

    Fails open: if an exception occurs during status checking, the
    request is allowed through (with error logged).
    """

    EXEMPT_PREFIXES = (
        "/static/",
        "/auth/",
        "/onboarding/",
        "/api/",
        "/accounts/",
        "/admin/",
        "/stripe/",
        "/media/",
    )

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only check authenticated, non-staff users
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_staff:
            return self.get_response(request)

        path = request.path

        # Skip non-dashboard routes (landing pages, admin, static, etc.)
        if not self._is_dashboard_route(path):
            # Still check explicit exempt prefixes for dashboard-adjacent routes
            if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
                return self.get_response(request)
            # Non-dashboard, non-exempt: let through (public landing pages)
            return self.get_response(request)

        # Check if path is exempt within dashboard scope
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        # Check setup status - fail open on errors
        try:
            from apps.identity.services import SetupStatusService

            status = SetupStatusService.get_setup_status(request.user)

            if not status.is_complete:
                # Redirect to the appropriate onboarding step
                redirect_url = status.redirect_url
                if path != redirect_url:
                    return HttpResponseRedirect(redirect_url)
        except Exception:
            logger.exception(
                "SetupStatusMiddleware error for user %s - failing open",
                request.user.email if hasattr(request.user, "email") else "unknown",
            )

        return self.get_response(request)


class DelinquentMiddleware(_DashboardOnlyMiddleware):
    """
    Middleware that restricts access for users with delinquent billing.

    Only applies to dashboard routes. Landing pages and other public
    routes are never intercepted — a delinquent user can still view
    public pages normally.

    If user.is_delinquent is True, only allows access to a limited set
    of dashboard paths (billing, support, logout, etc.) and redirects
    everything else to /delinquent/.
    """

    ALLOWED_PREFIXES = (
        "/delinquent/",
        "/auth/logout/",
        "/billing/",
        "/support/",
        "/api/billing/",
        "/static/",
        "/media/",
        "/admin/",
    )

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only check authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        # Skip non-dashboard routes (landing pages are always accessible)
        if not self._is_dashboard_route(path):
            return self.get_response(request)

        # Check delinquent status
        try:
            is_delinquent = getattr(request.user, "is_delinquent", False)

            if is_delinquent:
                # Allow access to permitted paths
                if any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                    return self.get_response(request)

                # Redirect to delinquent page
                return HttpResponseRedirect("/delinquent/")
        except Exception:
            logger.exception(
                "DelinquentMiddleware error for user %s - failing open",
                request.user.email if hasattr(request.user, "email") else "unknown",
            )

        return self.get_response(request)
