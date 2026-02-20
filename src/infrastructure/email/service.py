"""
Email service for sending transactional emails.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Result of email send operation."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailService:
    """
    Service for sending transactional emails.

    Supports:
    - Plain text and HTML emails
    - Template-based emails
    - Attachments
    - CC/BCC recipients
    """

    def __init__(self):
        self.default_from = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
        )

    def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None,
    ) -> EmailResult:
        """
        Send an email.

        Args:
            to: Recipient email(s)
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            from_email: Sender email (default: DEFAULT_FROM_EMAIL)
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to addresses
            attachments: List of (filename, content, mimetype) tuples

        Returns:
            EmailResult with success status
        """
        if isinstance(to, str):
            to = [to]

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email or self.default_from,
                to=to,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to,
            )

            if html_body:
                email.attach_alternative(html_body, "text/html")

            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)

            email.send(fail_silently=False)

            logger.info(f"Email sent to {to}: {subject}")
            return EmailResult(success=True)

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return EmailResult(success=False, error=str(e))

    def send_template(
        self,
        to: str | List[str],
        template_name: str,
        context: Dict[str, Any],
        subject: Optional[str] = None,
        **kwargs,
    ) -> EmailResult:
        """
        Send email using Django template.

        Args:
            to: Recipient email(s)
            template_name: Template name (without extension)
            context: Template context
            subject: Email subject (can also be in template)
            **kwargs: Additional args for send()

        Templates should be at:
            templates/emails/{template_name}.txt (plain text)
            templates/emails/{template_name}.html (HTML - optional)
        """
        # Render plain text
        body = render_to_string(f"emails/{template_name}.txt", context)

        # Try to render HTML (optional)
        html_body = None
        try:
            html_body = render_to_string(f"emails/{template_name}.html", context)
        except Exception:
            pass

        # Get subject from context if not provided
        resolved_subject: str = (
            subject or context.get("subject") or f"Email from {settings.SITE_NAME}"
        )

        return self.send(
            to=to, subject=resolved_subject, body=body, html_body=html_body, **kwargs
        )

    def send_welcome(self, user) -> EmailResult:
        """Send welcome email to new user."""
        return self.send_template(
            to=user.email,
            template_name="welcome",
            context={
                "user": user,
                "subject": "Bem-vindo ao Launch!",
            },
        )

    def send_password_reset(self, user, reset_url: str) -> EmailResult:
        """Send password reset email."""
        return self.send_template(
            to=user.email,
            template_name="password_reset",
            context={
                "user": user,
                "reset_url": reset_url,
                "subject": "Redefinição de senha",
            },
        )

    def send_email_verification(self, user, verification_url: str) -> EmailResult:
        """Send email verification link."""
        return self.send_template(
            to=user.email,
            template_name="email_verification",
            context={
                "user": user,
                "verification_url": verification_url,
                "subject": "Confirme seu email",
            },
        )


email_service = EmailService()
