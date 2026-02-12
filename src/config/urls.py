"""
URL configuration for Launch Inertia project.

All routes use Inertia.js for rendering React components.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Inertia pages
    path("", include("apps.identity.urls")),
    path("identities/", include("apps.contacts.urls")),
    path("billing/", include("apps.billing.urls")),
    path("notifications/", include("apps.notifications.urls")),
    # Django Allauth (for account management)
    path("accounts/", include("allauth.urls")),
    # Stripe webhooks
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
]

# Debug toolbar (development only) - disabled temporarily
if settings.DEBUG:
    # urlpatterns += [
    #     path("__debug__/", include("debug_toolbar.urls")),
    # ]
    # Serve static and media files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
