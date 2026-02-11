from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts.identity"
    label = "contact_identity"
    verbose_name = "Identity Resolution"

    def ready(self):
        from . import signals  # noqa: F401
