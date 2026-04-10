from django.apps import AppConfig


class CacheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infrastructure.cache"
    label = "infrastructure_cache"
    verbose_name = "Cache Infrastructure"
