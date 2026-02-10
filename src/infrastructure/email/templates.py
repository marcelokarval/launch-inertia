"""
Email template utilities.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class EmailTemplate:
    """
    Email template configuration.

    Usage:
        template = EmailTemplate(
            name="welcome",
            subject="Welcome to Launch!",
            default_context={"company": "Launch"}
        )
    """
    name: str
    subject: str
    default_context: Optional[Dict[str, Any]] = None

    def get_context(self, **extra) -> Dict[str, Any]:
        """Merge default context with extra context."""
        context = self.default_context.copy() if self.default_context else {}
        context.update(extra)
        context.setdefault("subject", self.subject)
        return context


# Pre-defined templates
WELCOME_TEMPLATE = EmailTemplate(
    name="welcome",
    subject="Bem-vindo ao Launch!",
    default_context={"company": "Launch"}
)

PASSWORD_RESET_TEMPLATE = EmailTemplate(
    name="password_reset",
    subject="Redefinição de senha",
)

EMAIL_VERIFICATION_TEMPLATE = EmailTemplate(
    name="email_verification",
    subject="Confirme seu email",
)

TERMS_UPDATED_TEMPLATE = EmailTemplate(
    name="terms_updated",
    subject="Termos de uso atualizados",
)
