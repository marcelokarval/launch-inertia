"""
Test settings with SQLite in-memory database.
Used for integrity testing without external dependencies.
"""

from .base import *  # noqa

# Override database to SQLite in-memory
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use local memory cache instead of Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable cacheops (requires Redis)
CACHEOPS_ENABLED = False
CACHEOPS = {}

# Use in-memory email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery: run tasks synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable Stripe for tests
STRIPE_TEST_SECRET_KEY = "sk_test_fake"
STRIPE_TEST_PUBLIC_KEY = "pk_test_fake"
DJSTRIPE_WEBHOOK_SECRET = "whsec_test_fake"

# Session backend that doesn't require cache
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging noise during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# Site name for tests
SITE_NAME = "Launch Test"
