"""
Redis cache client with typed operations.
"""
from typing import Any, Optional

from django.core.cache import cache
from django.conf import settings


class CacheClient:
    """
    Typed cache client wrapper around Django's cache framework.
    """

    def __init__(self, prefix: str = "launch"):
        self.prefix = prefix
        self.default_ttl = getattr(settings, "CACHE_DEFAULT_TTL", 3600)

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        return cache.get(self._make_key(key), default)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ttl = ttl or self.default_ttl
        return cache.set(self._make_key(key), value, ttl)

    def delete(self, key: str) -> bool:
        return cache.delete(self._make_key(key))

    def exists(self, key: str) -> bool:
        return cache.get(self._make_key(key)) is not None

    def get_or_set(self, key: str, default_func: callable, ttl: Optional[int] = None) -> Any:
        ttl = ttl or self.default_ttl
        return cache.get_or_set(self._make_key(key), default_func, ttl)

    def increment(self, key: str, delta: int = 1) -> int:
        try:
            return cache.incr(self._make_key(key), delta)
        except ValueError:
            self.set(key, delta)
            return delta

    def decrement(self, key: str, delta: int = 1) -> int:
        try:
            return cache.decr(self._make_key(key), delta)
        except ValueError:
            self.set(key, 0)
            return 0

    def delete_pattern(self, pattern: str) -> int:
        full_pattern = self._make_key(pattern)
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection("default")
            keys = conn.keys(full_pattern.replace("*", "*"))
            if keys:
                return conn.delete(*keys)
            return 0
        except (ImportError, Exception):
            return 0

    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        ttl = ttl or self.default_ttl
        prefixed = {self._make_key(k): v for k, v in mapping.items()}
        cache.set_many(prefixed, ttl)
        return True

    def get_many(self, keys: list[str]) -> dict:
        prefixed_keys = [self._make_key(k) for k in keys]
        result = cache.get_many(prefixed_keys)
        return {k.replace(f"{self.prefix}:", ""): v for k, v in result.items()}

    def clear(self) -> bool:
        cache.clear()
        return True


cache_client = CacheClient()
