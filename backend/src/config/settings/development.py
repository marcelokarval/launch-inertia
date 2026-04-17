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
    return path.startswith(("/app/", "/admin/", "/auth/", "/__debug__/"))


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": _show_toolbar,
    # Reduce overhead: don't intercept redirects
    "INTERCEPT_REDIRECTS": False,
}

# Explicitly list panels WITHOUT ProfilingPanel.
# ProfilingPanel uses cProfile which conflicts with Python 3.13 sys.monitoring
# (ValueError: "Another profiling tool is already active").
# DISABLE_PANELS only sets default state — browser cookie can re-enable it.
# Using DEBUG_TOOLBAR_PANELS removes the panel entirely from the chain.
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.alerts.AlertsPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    # ProfilingPanel intentionally excluded — Python 3.13 cProfile conflict
]
