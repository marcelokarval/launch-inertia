from django.apps import AppConfig


class LandingConfig(AppConfig):
    """Landing pages app — public capture, checkout, thank-you pages."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.landing"
    verbose_name = "Landing Pages"
