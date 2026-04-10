"""
Structured logging utilities.
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime

from django.conf import settings


class StructuredLogger:
    """
    Logger that outputs structured JSON logs.

    Useful for log aggregation systems (ELK, CloudWatch, etc.).
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.default_context: Dict[str, Any] = {}

    def _format_message(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format log message as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            **self.default_context,
            **(extra or {}),
        }
        return json.dumps(log_data)

    def set_context(self, **kwargs) -> None:
        """Set default context for all log messages."""
        self.default_context.update(kwargs)

    def clear_context(self) -> None:
        """Clear default context."""
        self.default_context = {}

    def debug(self, message: str, **extra) -> None:
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(self._format_message("DEBUG", message, extra))

    def info(self, message: str, **extra) -> None:
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(self._format_message("INFO", message, extra))

    def warning(self, message: str, **extra) -> None:
        if self.logger.isEnabledFor(logging.WARNING):
            self.logger.warning(self._format_message("WARNING", message, extra))

    def error(self, message: str, exc_info: bool = False, **extra) -> None:
        if self.logger.isEnabledFor(logging.ERROR):
            self.logger.error(
                self._format_message("ERROR", message, extra),
                exc_info=exc_info
            )

    def critical(self, message: str, exc_info: bool = True, **extra) -> None:
        if self.logger.isEnabledFor(logging.CRITICAL):
            self.logger.critical(
                self._format_message("CRITICAL", message, extra),
                exc_info=exc_info
            )

    def exception(self, message: str, **extra) -> None:
        """Log exception with traceback."""
        self.error(message, exc_info=True, **extra)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="usr_123", ip="1.2.3.4")
    """
    return StructuredLogger(name)


# Request context logger
class RequestLogger:
    """
    Logger that automatically includes request context.

    Usage in views:
        logger = RequestLogger(request)
        logger.info("Processing order")
    """

    def __init__(self, request):
        self.logger = get_logger("request")
        self.request = request

        # Set context from request
        self.logger.set_context(
            request_id=getattr(request, "request_id", None),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
            path=request.path,
            method=request.method,
            ip=self._get_client_ip(),
        )

    def _get_client_ip(self) -> str:
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR", "")

    def __getattr__(self, name):
        return getattr(self.logger, name)
