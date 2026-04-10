"""
Feature flags for conditional Django settings behavior.

Provides environment-aware settings that adapt to local/development/testing/staging/production.

Usage:
    from config.settings.flags import flags

    DEBUG = flags.debug
    ALLOWED_HOSTS = flags.allowed_hosts
"""

import os

from config.environment import (
    get_bool_env,
    get_list_env,
    get_int_env,
    is_development,
    is_production,
    is_testing,
    is_staging,
)


class FeatureFlags:
    """Feature flags for conditional Django settings."""

    # =========================================================================
    # Core Django
    # =========================================================================

    @property
    def debug(self) -> bool:
        if is_production():
            return False
        return get_bool_env("DEBUG", default=True)

    @property
    def secret_key(self) -> str:
        key = os.getenv("SECRET_KEY")
        if not key:
            if is_production():
                raise ValueError("SECRET_KEY must be set in production")
            key = "django-insecure-launch-dev-key-change-in-production"
        return key

    @property
    def allowed_hosts(self) -> list[str]:
        if is_development():
            # "*" allows LAN access (e.g., 192.168.x.x from mobile devices)
            # Safe in development only — production reads from env var.
            return ["*"]
        return get_list_env("ALLOWED_HOSTS", default=["localhost"])

    @property
    def csrf_trusted_origins(self) -> list[str]:
        if is_development():
            origins = [
                "http://localhost:8844",
                "http://127.0.0.1:8844",
                "http://localhost:3344",  # Dashboard Vite
                "http://127.0.0.1:3344",
                "http://localhost:3345",  # Landing Vite
                "http://127.0.0.1:3345",
            ]
            # Allow LAN IPs for mobile device testing (e.g., Android via Wi-Fi)
            extra = os.getenv("CSRF_TRUSTED_ORIGINS_EXTRA", "")
            if extra:
                origins.extend(extra.split(","))
            return origins
        return get_list_env("CSRF_TRUSTED_ORIGINS", default=[])

    # =========================================================================
    # Database
    # =========================================================================

    @property
    def db_name(self) -> str:
        return os.getenv("DB_NAME", "launch_inertia")

    @property
    def db_user(self) -> str:
        return os.getenv("DB_USER", "postgres")

    @property
    def db_password(self) -> str:
        return os.getenv("DB_PASSWORD", "postgres")

    @property
    def db_host(self) -> str:
        return os.getenv("DB_HOST", "localhost")

    @property
    def db_port(self) -> str:
        return os.getenv("DB_PORT", "5432")

    @property
    def db_conn_max_age(self) -> int:
        return get_int_env("DB_CONN_MAX_AGE", default=600 if is_production() else 0)

    # =========================================================================
    # Cache
    # =========================================================================

    @property
    def redis_url(self) -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # =========================================================================
    # Security
    # =========================================================================

    @property
    def secure_ssl_redirect(self) -> bool:
        return is_production()

    @property
    def secure_hsts_seconds(self) -> int:
        return 31536000 if is_production() else 0

    @property
    def session_cookie_secure(self) -> bool:
        return is_production()

    @property
    def csrf_cookie_secure(self) -> bool:
        return is_production()

    @property
    def session_cookie_samesite(self) -> str:
        return "Strict" if is_production() else "Lax"

    @property
    def csrf_cookie_samesite(self) -> str:
        return "Strict" if is_production() else "Lax"

    # =========================================================================
    # Email
    # =========================================================================

    @property
    def email_backend(self) -> str:
        if is_testing():
            return "django.core.mail.backends.locmem.EmailBackend"
        elif is_development():
            return "django.core.mail.backends.console.EmailBackend"
        return "django_ses.SESBackend"

    # =========================================================================
    # Celery
    # =========================================================================

    @property
    def celery_broker_url(self) -> str:
        return os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

    @property
    def celery_task_eager(self) -> bool:
        return is_testing()

    # =========================================================================
    # Stripe
    # =========================================================================

    @property
    def stripe_live_mode(self) -> bool:
        if is_development() or is_testing():
            return False
        return get_bool_env("STRIPE_LIVE_MODE", default=False)

    # =========================================================================
    # Logging
    # =========================================================================

    @property
    def log_level(self) -> str:
        if is_development():
            return "DEBUG"
        elif is_testing():
            return "WARNING"
        return os.getenv("LOG_LEVEL", "INFO")

    # =========================================================================
    # Vite
    # =========================================================================

    @property
    def vite_dev_server_url(self) -> str:
        return os.getenv("VITE_DEV_URL", "http://localhost:3344")

    # =========================================================================
    # Landing / Migration Runtime
    # =========================================================================

    @property
    def landing_json_fallback_enabled(self) -> bool:
        """Whether legacy JSON campaign fallback is allowed at runtime.

        Production should converge to DB-backed CapturePage configs only.
        Dev/test keep JSON fallback enabled by default during migration.
        """
        default = not is_production()
        return get_bool_env("LANDING_JSON_FALLBACK_ENABLED", default=default)

    @property
    def lead_outbox_failed_threshold(self) -> int:
        return get_int_env("LEAD_OUTBOX_FAILED_THRESHOLD", default=5)

    @property
    def lead_outbox_pending_threshold(self) -> int:
        return get_int_env("LEAD_OUTBOX_PENDING_THRESHOLD", default=10)

    @property
    def lead_outbox_pending_max_age_minutes(self) -> int:
        return get_int_env("LEAD_OUTBOX_PENDING_MAX_AGE_MINUTES", default=30)

    @property
    def lead_outbox_n8n_slo_minutes(self) -> int:
        return get_int_env("LEAD_OUTBOX_N8N_SLO_MINUTES", default=10)

    @property
    def lead_outbox_meta_capi_slo_minutes(self) -> int:
        return get_int_env("LEAD_OUTBOX_META_CAPI_SLO_MINUTES", default=15)


# Global instance
flags = FeatureFlags()
