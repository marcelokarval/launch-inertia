"""
Cache decorators for function/method caching.
"""
import functools
from typing import Optional, Callable, Any

from .client import cache_client


def cached(ttl: int = 3600, key_prefix: str = "", key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=300, key_prefix="user")
        def get_user(user_id: int):
            return User.objects.get(id=user_id)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                start_idx = 1 if args and hasattr(args[0], '__class__') else 0
                for arg in args[start_idx:]:
                    key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")
                cache_key = ":".join(key_parts)

            cached_value = cache_client.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache_client.set(cache_key, result, ttl)
            return result

        def invalidate(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [key_prefix or func.__name__]
                start_idx = 1 if args and hasattr(args[0], '__class__') else 0
                for arg in args[start_idx:]:
                    key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")
                cache_key = ":".join(key_parts)
            cache_client.delete(cache_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def cache_invalidate(key_pattern: str):
    """Decorator to invalidate cache after function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            if "*" in key_pattern:
                cache_client.delete_pattern(key_pattern)
            else:
                cache_client.delete(key_pattern)
            return result
        return wrapper
    return decorator
