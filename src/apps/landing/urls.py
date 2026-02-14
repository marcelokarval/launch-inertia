"""
Landing page URL configuration.

These routes are public (no auth required).
Mounted at the root "/" in config/urls.py.
"""

from django.urls import path

from apps.landing import views

app_name = "landing"

urlpatterns = [
    path("", views.home, name="home"),
]
