"""
Security headers middleware.
"""

from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """
    Adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: (configurable)
    - Content-Security-Policy: (configurable)

    Settings:
        SECURITY_HEADERS_ENABLED: bool (default: True)
        SECURITY_CSP_POLICY: str (Content-Security-Policy value)
        SECURITY_PERMISSIONS_POLICY: str (Permissions-Policy value)

    Usage in settings.py:
        MIDDLEWARE = [
            ...
            'core.security.middleware.SecurityHeadersMiddleware',
            ...
        ]
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.enabled = getattr(settings, "SECURITY_HEADERS_ENABLED", True)

        # CSP policy (customize for your needs)
        self.csp_policy = getattr(
            settings,
            "SECURITY_CSP_POLICY",
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "font-src 'self' https:; connect-src 'self' https:;",
        )

        # Permissions policy
        self.permissions_policy = getattr(
            settings,
            "SECURITY_PERMISSIONS_POLICY",
            "geolocation=(), microphone=(), camera=()",
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if not self.enabled:
            return response

        # Basic security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        if self.permissions_policy:
            response["Permissions-Policy"] = self.permissions_policy

        # Content Security Policy (only in production — DEBUG=False)
        # In dev, Vite HMR loads scripts from localhost:3344 which CSP would block
        content_type = response.get("Content-Type", "")
        if "text/html" in content_type and self.csp_policy and not settings.DEBUG:
            response["Content-Security-Policy"] = self.csp_policy

        # HSTS (only in production with HTTPS)
        if not settings.DEBUG and request.is_secure():
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
