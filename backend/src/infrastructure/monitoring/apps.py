from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infrastructure.monitoring"
    label = "infrastructure_monitoring"
    verbose_name = "Monitoring & Observability"
