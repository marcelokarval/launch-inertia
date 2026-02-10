"""
Email service for sending transactional emails.
"""
from .service import EmailService, email_service
from .templates import EmailTemplate

__all__ = [
    "EmailService",
    "email_service",
    "EmailTemplate",
]
