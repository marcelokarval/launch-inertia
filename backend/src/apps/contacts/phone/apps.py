from django.apps import AppConfig


class ContactPhoneConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts.phone"
    label = "contact_phone"
    verbose_name = "Contact Phones"

    def ready(self):
        from . import signals  # noqa: F401
