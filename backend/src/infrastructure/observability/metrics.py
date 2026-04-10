"""
Simple metrics collection utilities.
"""
import time
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import contextmanager

from django.core.cache import cache


class MetricsCollector:
    """
    Simple metrics collector using cache backend.

    For production, consider using Prometheus, StatsD, or similar.
    """

    def __init__(self, prefix: str = "metrics"):
        self.prefix = prefix

    def _key(self, name: str) -> str:
        return f"{self.prefix}:{name}"

    def increment(self, name: str, value: int = 1, tags: Optional[Dict] = None) -> None:
        """Increment a counter metric."""
        key = self._key(name)
        try:
            cache.incr(key, value)
        except ValueError:
            cache.set(key, value, timeout=None)

    def gauge(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """Set a gauge metric value."""
        key = self._key(name)
        cache.set(key, value, timeout=None)

    def timing(self, name: str, value_ms: float, tags: Optional[Dict] = None) -> None:
        """Record a timing metric in milliseconds."""
        # Store as list of recent timings for averaging
        key = self._key(f"{name}:timings")
        timings = cache.get(key) or []
        timings.append(value_ms)
        # Keep last 100 timings
        timings = timings[-100:]
        cache.set(key, timings, timeout=3600)

    @contextmanager
    def timer(self, name: str, tags: Optional[Dict] = None):
        """
        Context manager to time a block of code.

        Usage:
            with metrics.timer("database.query"):
                result = db.execute(query)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.timing(name, elapsed_ms, tags)

    def timed(self, name: Optional[str] = None):
        """
        Decorator to time function execution.

        Usage:
            @metrics.timed("api.process_order")
            def process_order(order_id):
                ...
        """
        def decorator(func):
            metric_name = name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.timer(metric_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def get(self, name: str) -> Any:
        """Get current value of a metric."""
        return cache.get(self._key(name))

    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a timing metric."""
        timings = cache.get(self._key(f"{name}:timings")) or []
        if not timings:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        return {
            "count": len(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }


# Global metrics instance
metrics = MetricsCollector()


# Common metric helpers
def track_request(view_name: str) -> None:
    """Track a request to a view."""
    metrics.increment(f"requests.{view_name}")
    metrics.increment("requests.total")


def track_error(error_type: str) -> None:
    """Track an error occurrence."""
    metrics.increment(f"errors.{error_type}")
    metrics.increment("errors.total")


def track_login(success: bool) -> None:
    """Track login attempts."""
    if success:
        metrics.increment("auth.login.success")
    else:
        metrics.increment("auth.login.failed")
