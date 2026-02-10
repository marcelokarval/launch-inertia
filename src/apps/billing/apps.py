from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    label = "billing"
    verbose_name = "Billing & Payments"

    def ready(self):
        from . import signals  # noqa: F401 — registers webhook receivers
