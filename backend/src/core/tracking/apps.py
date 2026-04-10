"""Tracking app configuration."""

from django.apps import AppConfig


class TrackingConfig(AppConfig):
    name = "core.tracking"
    verbose_name = "Tracking"
    default_auto_field = "django.db.models.BigAutoField"
