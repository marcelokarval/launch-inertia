from django.apps import AppConfig


class ContactEmailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts.email"
    label = "contact_email"
    verbose_name = "Contact Emails"

    def ready(self):
        from . import signals  # noqa: F401
