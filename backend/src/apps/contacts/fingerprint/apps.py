from django.apps import AppConfig


class FingerprintConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts.fingerprint"
    label = "contact_fingerprint"
    verbose_name = "Device Fingerprints"

    def ready(self):
        from . import signals  # noqa: F401
