from django.apps import AppConfig


class EmailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infrastructure.email"
    label = "infrastructure_email"
    verbose_name = "Email Infrastructure"
