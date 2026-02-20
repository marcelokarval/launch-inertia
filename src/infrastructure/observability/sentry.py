"""
Sentry error tracking integration.
"""

import logging
from typing import Any, Dict, Literal, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Sentry SDK is optional
_sentry_initialized = False

try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


def init_sentry() -> bool:
    """
    Initialize Sentry SDK.

    Should be called in settings or wsgi/asgi.

    Returns:
        True if initialized successfully
    """
    global _sentry_initialized

    if _sentry_initialized:
        return True

    if not SENTRY_AVAILABLE or sentry_sdk is None:
        logger.warning("Sentry SDK not installed. Error tracking disabled.")
        return False

    dsn = getattr(settings, "SENTRY_DSN", None)
    if not dsn:
        logger.info("SENTRY_DSN not configured. Error tracking disabled.")
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            environment=getattr(settings, "ENVIRONMENT", "development"),
            release=getattr(settings, "APP_VERSION", "unknown"),
            traces_sample_rate=getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1),
            profiles_sample_rate=getattr(settings, "SENTRY_PROFILES_SAMPLE_RATE", 0.1),
            send_default_pii=False,  # LGPD/GDPR compliance
        )
        _sentry_initialized = True
        logger.info("Sentry initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def capture_exception(
    error: Exception,
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        error: The exception to capture
        extra: Additional context data
        tags: Tags for filtering in Sentry

    Returns:
        Event ID if captured, None otherwise

    Usage:
        try:
            do_something()
        except Exception as e:
            capture_exception(e, extra={"user_id": user.id})
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized or sentry_sdk is None:
        logger.error(f"Exception (Sentry not available): {error}", exc_info=True)
        return None

    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        return sentry_sdk.capture_exception(error)


LogLevel = Literal["debug", "info", "warning", "error", "fatal", "critical"]


def capture_message(
    message: str,
    level: LogLevel = "info",
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        extra: Additional context data
        tags: Tags for filtering

    Returns:
        Event ID if captured, None otherwise
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized or sentry_sdk is None:
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            f"Message (Sentry not available): {message}",
        )
        return None

    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        return sentry_sdk.capture_message(message, level=level)  # type: ignore[arg-type]


def set_user(user) -> None:
    """
    Set user context for Sentry events.

    Call this after user authentication.
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized or sentry_sdk is None:
        return

    if user and user.is_authenticated:
        sentry_sdk.set_user(
            {
                "id": str(user.public_id),
                "email": user.email,
            }
        )
    else:
        sentry_sdk.set_user(None)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict] = None,
) -> None:
    """
    Add a breadcrumb for debugging.

    Breadcrumbs are trails of events leading up to an error.
    """
    if not SENTRY_AVAILABLE or not _sentry_initialized or sentry_sdk is None:
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )
