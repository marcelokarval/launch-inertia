"""
Django development settings.

Most settings are handled by FeatureFlags in base.py.
This file only contains development-specific overrides.
"""

from .base import *  # noqa: F401, F403

# Development apps (debug toolbar)
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]


def _show_toolbar(request) -> bool:  # type: ignore[no-untyped-def]
    """Show DjDT only for dashboard/admin routes, not public landing pages.

    Landing pages are high-traffic, public-facing — DjDT overhead is
    unacceptable there. Use ?djdt query param to force-enable on any route.
    """
    if not DEBUG:  # noqa: F405
        return False
    # Force-enable with ?djdt on any page (for debugging landing pages)
    if request.GET.get("djdt") == "1":
        return True
    # Only show on dashboard and admin routes by default
    path = request.path
    return path.startswith(
        ("/app/", "/admin/", "/auth/", "/onboarding/", "/__debug__/")
    )


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": _show_toolbar,
    # Disable profiling panel — conflicts with Python 3.13 sys.monitoring
    # (ValueError: "Another profiling tool is already active")
    "DISABLE_PANELS": {
        "debug_toolbar.panels.profiling.ProfilingPanel",
    },
    # Reduce overhead: don't intercept redirects
    "INTERCEPT_REDIRECTS": False,
}
