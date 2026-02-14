"""
Landing page URL configuration.

These routes are public (no auth required).
Mounted at the root "/" in config/urls.py — must be LAST.
"""

from django.urls import path

from apps.landing import views

app_name = "landing"

urlpatterns = [
    # Capture pages
    path(
        "inscrever/<slug:campaign_slug>/",
        views.capture_page,
        name="capture",
    ),
    # Thank-you pages (placeholder — full implementation in Phase F)
    path(
        "obrigado/<slug:campaign_slug>/",
        views.thank_you_page,
        name="thank_you",
    ),
    # Home page (last — catch-all for root "/")
    path("", views.home, name="home"),
]
