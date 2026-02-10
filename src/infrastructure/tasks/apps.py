from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infrastructure.tasks"
    label = "infrastructure_tasks"
    verbose_name = "Background Tasks"
