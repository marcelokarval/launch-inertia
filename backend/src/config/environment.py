"""Environment configuration module.

Handles loading and processing of environment variables with support
for variable substitution (e.g., ${VAR_NAME}) and multi-environment configuration.

Architecture:
    - Supports APP_ENV to select environment-specific configuration
    - Loads .env file from project root
    - Supports variable expansion like ${VAR_NAME}

Environments:
    - local: Local development (default if APP_ENV not set)
    - development: Shared development environment
    - testing: Automated tests / CI/CD
    - staging: Pre-production / QA
    - production: Production (security hardened)
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Build paths inside the backend project
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/src/config/ -> backend/src/
PROJECT_ROOT = BASE_DIR.parent  # backend/
WORKSPACE_ROOT = PROJECT_ROOT.parent  # launch-inertia/

# Environment detection
APP_ENV = os.getenv("APP_ENV", "local")

logger = logging.getLogger(__name__)


def expand_variables(value: str, context: dict[str, str]) -> str:
    """Expand variables in format ${VAR_NAME} using context."""
    if not isinstance(value, str):
        return value

    pattern = r"\$\{([^}]+)\}"

    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in context:
            return context[var_name]
        elif var_name in os.environ:
            return os.environ[var_name]
        else:
            logger.warning(
                f"Variable ${{{var_name}}} not found in context or environment"
            )
            return match.group(0)

    return re.sub(pattern, replace_var, value)


def load_environment() -> None:
    """Load environment variables from .env file."""
    candidate_files = [
        PROJECT_ROOT / ".env",  # preferred: backend/.env
        WORKSPACE_ROOT / ".env",  # fallback: repo root/.env
    ]

    for env_file in candidate_files:
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
            return

    logger.warning(
        "Environment file not found in any candidate path: %s",
        ", ".join(str(path) for path in candidate_files),
    )


def get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, "").lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int = 0) -> int:
    """Get integer environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_list_env(
    key: str, default: Optional[list[str]] = None, separator: str = ","
) -> list[str]:
    """Get list environment variable."""
    if default is None:
        default = []
    value = os.getenv(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_environment() -> str:
    """Get current environment name."""
    return APP_ENV


def is_development() -> bool:
    """Check if running in development environment."""
    return APP_ENV in ("local", "development")


def is_production() -> bool:
    """Check if running in production environment."""
    return APP_ENV == "production"


def is_testing() -> bool:
    """Check if running in testing environment."""
    return APP_ENV == "testing"


def is_staging() -> bool:
    """Check if running in staging environment."""
    return APP_ENV == "staging"


# Load environment on module import
load_environment()
