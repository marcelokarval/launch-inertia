from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.identity"
    label = "identity"
    verbose_name = "Identity & Auth"

    def ready(self):
        from . import signals  # noqa: F401 — registers signal receivers
