"""
Django development settings.

Most settings are handled by FeatureFlags in base.py.
This file only contains development-specific overrides.
"""

from .base import *  # noqa: F401, F403

# Development apps (debug toolbar)
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,  # noqa: F405
}
