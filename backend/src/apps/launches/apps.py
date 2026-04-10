from django.apps import AppConfig


class LaunchesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.launches"
    verbose_name = "Launches"

    def ready(self) -> None:
        from apps.launches import signals  # noqa: F401
