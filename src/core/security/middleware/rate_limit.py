"""
Rate limiting middleware.
"""
import time
import logging
from typing import Optional, Callable

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Simple rate limiting middleware using cache backend.

    Limits requests per IP address within a time window.

    Settings:
        RATE_LIMIT_ENABLED: bool (default: True)
        RATE_LIMIT_REQUESTS: int (default: 100)
        RATE_LIMIT_WINDOW: int (seconds, default: 60)
        RATE_LIMIT_WHITELIST: list of IPs to exclude

    Usage in settings.py:
        MIDDLEWARE = [
            ...
            'core.security.middleware.RateLimitMiddleware',
            ...
        ]
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.enabled = getattr(settings, "RATE_LIMIT_ENABLED", True)
        self.max_requests = getattr(settings, "RATE_LIMIT_REQUESTS", 100)
        self.window = getattr(settings, "RATE_LIMIT_WINDOW", 60)
        self.whitelist = set(getattr(settings, "RATE_LIMIT_WHITELIST", []))

        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/health/",
            "/ready/",
            "/static/",
            "/media/",
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled:
            return self.get_response(request)

        # Skip excluded paths
        if any(request.path.startswith(p) for p in self.excluded_paths):
            return self.get_response(request)

        ip = self._get_client_ip(request)

        # Skip whitelisted IPs
        if ip in self.whitelist:
            return self.get_response(request)

        # Check rate limit
        if self._is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return self._rate_limit_response(ip)

        # Increment request count
        self._increment_request_count(ip)

        response = self.get_response(request)

        # Add rate limit headers
        remaining, reset_time = self._get_rate_limit_info(ip)
        response["X-RateLimit-Limit"] = str(self.max_requests)
        response["X-RateLimit-Remaining"] = str(max(0, remaining))
        response["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _get_cache_key(self, ip: str) -> str:
        """Generate cache key for IP."""
        return f"rate_limit:{ip}"

    def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP has exceeded rate limit."""
        key = self._get_cache_key(ip)
        data = cache.get(key)

        if not data:
            return False

        count = data.get("count", 0)
        return count >= self.max_requests

    def _increment_request_count(self, ip: str) -> None:
        """Increment request count for IP."""
        key = self._get_cache_key(ip)
        data = cache.get(key)

        if data:
            data["count"] += 1
            # Use remaining TTL
            ttl = max(1, int(data["reset_at"] - time.time()))
            cache.set(key, data, ttl)
        else:
            reset_at = time.time() + self.window
            cache.set(key, {"count": 1, "reset_at": reset_at}, self.window)

    def _get_rate_limit_info(self, ip: str) -> tuple[int, int]:
        """Get remaining requests and reset time."""
        key = self._get_cache_key(ip)
        data = cache.get(key)

        if not data:
            return self.max_requests, int(time.time() + self.window)

        remaining = self.max_requests - data.get("count", 0)
        reset_at = int(data.get("reset_at", time.time() + self.window))

        return remaining, reset_at

    def _rate_limit_response(self, ip: str) -> HttpResponse:
        """Return rate limit exceeded response."""
        _, reset_time = self._get_rate_limit_info(ip)
        retry_after = max(1, reset_time - int(time.time()))

        response = JsonResponse(
            {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please try again in {retry_after} seconds.",
                "retry_after": retry_after,
            },
            status=429
        )
        response["Retry-After"] = str(retry_after)
        response["X-RateLimit-Limit"] = str(self.max_requests)
        response["X-RateLimit-Remaining"] = "0"
        response["X-RateLimit-Reset"] = str(reset_time)

        return response
