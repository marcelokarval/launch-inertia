"""
Django base settings for Launch Inertia project.

Uses FeatureFlags for environment-aware configuration.
All settings flow through flags for consistency.
"""

import os
import socket
from pathlib import Path

from config.environment import is_development, load_environment
from config.settings.flags import flags

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SRC_DIR = BASE_DIR / "src"

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

SECRET_KEY = flags.secret_key
DEBUG = flags.debug
ALLOWED_HOSTS = flags.allowed_hosts
SITE_ID = 1
SITE_NAME = "Launch"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

CORE_APPS = [
    "core.shared",
]

PRE_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    # CORS
    "corsheaders",
    # Inertia.js
    "inertia",
    # Vite integration
    "django_vite",
    # Authentication (social only - regular auth is custom)
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Background tasks
    "django_celery_beat",
    "django_celery_results",
    # Utilities
    "django_extensions",
    "import_export",
    # Stripe
    "djstripe",
]

PROJECT_APPS = [
    "apps.identity",
    "apps.contacts",
    # Contact sub-apps (identity resolution system)
    "apps.contacts.identity",
    "apps.contacts.email",
    "apps.contacts.phone",
    "apps.contacts.fingerprint",
    "apps.billing",
    "apps.notifications",
    "apps.landing",
    "apps.launches",
    "apps.ads",
]

CORE_FRAMEWORK_APPS = [
    "core.tracking",
]

INFRASTRUCTURE_APPS = [
    "infrastructure.cache",
    "infrastructure.email",
    "infrastructure.tasks",
    "infrastructure.monitoring",
]

INSTALLED_APPS = (
    CORE_APPS
    + PRE_APPS
    + DJANGO_APPS
    + THIRD_PARTY_APPS
    + PROJECT_APPS
    + CORE_FRAMEWORK_APPS
    + INFRASTRUCTURE_APPS
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    # Django standard
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Security (custom)
    "core.security.middleware.SecurityHeadersMiddleware",
    "core.security.middleware.RateLimitMiddleware",
    # Visitor tracking (identification, device profiling, GeoIP)
    "core.tracking.middleware.VisitorMiddleware",
    # Session-based anonymous identity (creates/recovers Identity per visitor)
    "core.tracking.identity_middleware.IdentitySessionMiddleware",
    # Inertia.js
    "inertia.middleware.InertiaMiddleware",
    # JSON body parser (request.data)
    "core.inertia.middleware.InertiaJsonParserMiddleware",
    # Custom shared data
    "core.inertia.middleware.InertiaShareMiddleware",
    # Custom guards
    "core.inertia.middleware.SetupStatusMiddleware",
    "core.inertia.middleware.DelinquentMiddleware",
    # Allauth (must be last)
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": flags.db_name,
        "USER": flags.db_user,
        "PASSWORD": flags.db_password,
        "HOST": flags.db_host,
        "PORT": flags.db_port,
        "CONN_MAX_AGE": flags.db_conn_max_age,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = "identity.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Django Allauth - configured for SOCIAL AUTH ONLY
# Regular login/register uses custom AuthService/RegistrationService
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"  # We handle verification ourselves
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True

# Social auth providers
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "APP": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_OAUTH_SECRET", ""),
        },
    }
}

LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/app/"
LOGOUT_REDIRECT_URL = "/auth/login/"

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    SRC_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# DJANGO VITE CONFIGURATION (multi-app)
# =============================================================================

_VITE_DEV_HOST = "localhost"


def _detect_vite_dev_mode(port: int) -> bool:
    """Auto-detect if a Vite dev server is running on the given port.

    Priority:
    1. Explicit DJANGO_VITE_DEV_MODE env var (overrides auto-detection)
    2. Non-dev environments (production/staging) -> always False
    3. TCP socket check to Vite dev server (<100ms timeout)
    """
    explicit = os.getenv("DJANGO_VITE_DEV_MODE", "").lower()
    if explicit in ("true", "1", "yes"):
        return True
    if explicit in ("false", "0", "no"):
        return False
    if not is_development():
        return False
    try:
        with socket.create_connection((_VITE_DEV_HOST, port), timeout=0.1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


DJANGO_VITE = {
    "dashboard": {
        "dev_mode": _detect_vite_dev_mode(port=3344),
        "dev_server_protocol": "http",
        "dev_server_host": _VITE_DEV_HOST,
        "dev_server_port": 3344,
        "static_url_prefix": "dashboard",
        "manifest_path": SRC_DIR / "static" / "dashboard" / ".vite" / "manifest.json",
    },
    "landing": {
        "dev_mode": _detect_vite_dev_mode(port=3345),
        "dev_server_protocol": "http",
        "dev_server_host": _VITE_DEV_HOST,
        "dev_server_port": 3345,
        "static_url_prefix": "landing",
        "manifest_path": SRC_DIR / "static" / "landing" / ".vite" / "manifest.json",
    },
}

# =============================================================================
# INERTIA.JS CONFIGURATION
# =============================================================================

# Default layout used by dashboard views.
# Landing views must pass template_name="landing.html" explicitly.
INERTIA_LAYOUT = "dashboard.html"
INERTIA_SSR_ENABLED = False
INERTIA_SSR_URL = "http://localhost:13714"
INERTIA_VERSION = "1.0"

# Layout map for the inertia_render helper
INERTIA_LAYOUTS = {
    "dashboard": "dashboard.html",
    "landing": "landing.html",
}

# =============================================================================
# CSRF CONFIGURATION
# =============================================================================

CSRF_COOKIE_NAME = "XSRF-TOKEN"
CSRF_HEADER_NAME = "HTTP_X_XSRF_TOKEN"
CSRF_COOKIE_HTTPONLY = False  # Axios/Inertia MUST read this cookie via JS
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = flags.csrf_trusted_origins

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = flags.session_cookie_samesite
SESSION_COOKIE_SECURE = flags.session_cookie_secure

# Session TTL: 90 days base. Extended dynamically by IdentitySessionMiddleware
# based on identity richness (visitor_id → 180d, email → 365d).
SESSION_COOKIE_AGE = 60 * 60 * 24 * 90  # 90 days

# Renew session TTL on every request — keeps active visitors alive.
SESSION_SAVE_EVERY_REQUEST = True

# =============================================================================
# SECURITY
# =============================================================================

SECURE_SSL_REDIRECT = flags.secure_ssl_redirect
SECURE_HSTS_SECONDS = flags.secure_hsts_seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = True if flags.secure_hsts_seconds > 0 else False
SECURE_HSTS_PRELOAD = True if flags.secure_hsts_seconds > 0 else False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_SECURE = flags.csrf_cookie_secure
CSRF_COOKIE_SAMESITE = flags.csrf_cookie_samesite

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": flags.redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}

# Cacheops configuration
CACHEOPS_REDIS = flags.redis_url
CACHEOPS_DEFAULTS = {
    "timeout": 60 * 15,
}
CACHEOPS = {
    "auth.user": {"ops": "get", "timeout": 60 * 15},
    "identity.*": {"ops": "all", "timeout": 60 * 15},
    "contacts.*": {"ops": "all", "timeout": 60 * 5},
    "notifications.*": {"ops": "all", "timeout": 60 * 5},
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = flags.celery_broker_url
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_ALWAYS_EAGER = flags.celery_task_eager
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Default periodic tasks (also manageable via django-celery-beat admin)
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-tokens": {
        "task": "identity.cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
    },
    "cleanup-old-notifications": {
        "task": "notifications.cleanup_old_notifications",
        "schedule": crontab(
            hour=4, minute=0, day_of_week=0
        ),  # Weekly on Sunday at 4:00 AM
        "kwargs": {"days": 90},
    },
    "batch-merge-recent-identities": {
        "task": "identity.batch_merge_recent",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "kwargs": {"lookback_days": 7},
    },
}

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = flags.email_backend
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@launch.app")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# AWS SES settings (production)
AWS_SES_REGION_NAME = os.getenv("AWS_SES_REGION_NAME", "us-east-1")
AWS_SES_REGION_ENDPOINT = f"email.{AWS_SES_REGION_NAME}.amazonaws.com"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# =============================================================================
# STRIPE CONFIGURATION
# =============================================================================

STRIPE_LIVE_MODE = flags.stripe_live_mode
STRIPE_LIVE_SECRET_KEY = os.getenv("STRIPE_LIVE_SECRET_KEY", "")
STRIPE_LIVE_PUBLIC_KEY = os.getenv("STRIPE_LIVE_PUBLIC_KEY", "")
STRIPE_TEST_SECRET_KEY = os.getenv("STRIPE_TEST_SECRET_KEY", "")
STRIPE_TEST_PUBLIC_KEY = os.getenv("STRIPE_TEST_PUBLIC_KEY", "")
DJSTRIPE_WEBHOOK_SECRET = os.getenv("DJSTRIPE_WEBHOOK_SECRET", "")
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": flags.log_level if not flags.debug else "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if flags.debug else "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_ENABLED = not flags.debug
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_WHITELIST = ["127.0.0.1"] if flags.debug else []

# Security headers
SECURITY_HEADERS_ENABLED = True

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8844",
    "http://127.0.0.1:8844",
    "http://localhost:3344",  # Dashboard Vite
    "http://127.0.0.1:3344",
    "http://localhost:3345",  # Landing Vite
    "http://127.0.0.1:3345",
]
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# DJANGO UNFOLD ADMIN
# =============================================================================

UNFOLD = {
    "SITE_TITLE": "Launch Admin",
    "SITE_HEADER": "Launch",
    "SITE_SYMBOL": "rocket_launch",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "config.settings.base.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {
                        "title": "Home",
                        "icon": "home",
                        "link": "/admin/",
                    },
                ],
            },
            {
                "title": "Users & Auth",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": "/admin/identity/user/",
                    },
                ],
            },
            {
                "title": "Identity",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Identities",
                        "icon": "fingerprint",
                        "link": "/admin/contact_identity/identity/",
                    },
                ],
            },
            {
                "title": "Billing",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Subscriptions",
                        "icon": "credit_card",
                        "link": "/admin/djstripe/subscription/",
                    },
                ],
            },
        ],
    },
}


# =============================================================================
# GEOIP (MaxMind GeoLite2)
# =============================================================================

GEOIP_CITY_DB = os.getenv(
    "GEOIP_CITY_DB", str(BASE_DIR / "data" / "GeoLite2-City.mmdb")
)
GEOIP_ASN_DB = os.getenv("GEOIP_ASN_DB", str(BASE_DIR / "data" / "GeoLite2-ASN.mmdb"))


def environment_callback(request):
    """Return environment badge for admin."""
    from django.conf import settings

    if settings.DEBUG:
        return ["Development", "warning"]
    return ["Production", "success"]
