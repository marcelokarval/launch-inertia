"""
URL configuration for Launch Inertia project.

All routes use Inertia.js for rendering React components.

URL structure:
  /app/*           - Dashboard (authenticated, guarded by middleware)
  /auth/*          - Authentication (pre-login)
  /admin/          - Django Admin (staff only)
  /accounts/       - Django Allauth (Google OAuth)
  /stripe/         - djstripe webhooks
  /                - Landing pages (public, added in Phase C)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.identity.urls import (
    auth_urlpatterns,
    dashboard_urlpatterns,
)

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Auth pages (pre-login) — /auth/*
    *auth_urlpatterns,
    # Dashboard (authenticated) — /app/*
    path("app/", include((dashboard_urlpatterns, "identity"))),
    path("app/identities/", include("apps.contacts.urls")),
    path("app/billing/", include("apps.billing.urls")),
    path("app/notifications/", include("apps.notifications.urls")),
    # Django Allauth (for account management)
    path("accounts/", include("allauth.urls")),
    # Stripe webhooks
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    # Landing pages (public) — must be LAST (catch-all at root)
    path("", include("apps.landing.urls")),
]

# Debug toolbar + static files (development only)
if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
