"""
Django production settings.

Most settings are handled by FeatureFlags in base.py.
This file only contains production-specific overrides.
"""

from .base import *  # noqa: F401, F403

# Ensure HTTPS proxy header is recognized
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =============================================================================
# STATIC FILES (S3/CloudFront) - Uncomment when ready
# =============================================================================

# STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
# AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")  # noqa: F405
# AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_CLOUDFRONT_DOMAIN")  # noqa: F405
# STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"

# =============================================================================
# MEDIA FILES (S3) - Uncomment when ready
# =============================================================================

# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = "private"

# =============================================================================
# SENTRY
# =============================================================================

import os

SENTRY_DSN = os.getenv("SENTRY_DSN", "")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
    )

# =============================================================================
# STRIPE (Live mode warning)
# =============================================================================

if not STRIPE_LIVE_MODE:  # noqa: F405
    import warnings

    warnings.warn(
        "STRIPE_LIVE_MODE is not enabled in production. "
        "Set STRIPE_LIVE_MODE=true if you want to process real payments."
    )
