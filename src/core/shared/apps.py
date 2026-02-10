from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.shared"
    label = "core_shared"
    verbose_name = "Core Shared"
