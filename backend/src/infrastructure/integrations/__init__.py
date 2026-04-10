"""
Third-party API integrations.

Add your external API clients here:
- Payment providers (Stripe, etc.)
- SMS services (Twilio, etc.)
- External APIs
"""
from .base import BaseAPIClient, APIResponse

__all__ = [
    "BaseAPIClient",
    "APIResponse",
]
