"""
Celery tasks for the identity app.

Tasks for:
- Sending verification emails asynchronously
- Sending password reset emails asynchronously
- Sending welcome emails asynchronously
- Cleaning up expired tokens periodically
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="identity.send_verification_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_verification_email_task(self, user_id: int, display_token: str):
    """
    Send email verification OTP to user.

    Args:
        user_id: The database PK of the user.
        display_token: The 6-digit OTP to include in the email.
    """
    try:
        from apps.identity.models import User
        from infrastructure.email.service import email_service

        user = User.objects.get(pk=user_id)

        result = email_service.send_template(
            to=user.email,
            template_name="email_verification",
            context={
                "user": user,
                "verification_code": display_token,
                "subject": "Confirme seu email",
            },
        )

        if result.success:
            logger.info("Verification email sent to user=%s", user.public_id)
        else:
            logger.warning(
                "Verification email failed for user=%s: %s",
                user.public_id,
                result.error,
            )
            raise Exception(f"Email send failed: {result.error}")

    except User.DoesNotExist:
        logger.error("send_verification_email: User pk=%s not found", user_id)
    except Exception as exc:
        logger.exception("send_verification_email failed for user_id=%s", user_id)
        raise self.retry(exc=exc)


@shared_task(
    name="identity.send_password_reset_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_password_reset_email_task(self, user_id: int, display_token: str):
    """
    Send password reset OTP to user.

    Args:
        user_id: The database PK of the user.
        display_token: The 6-digit OTP for password reset.
    """
    try:
        from apps.identity.models import User
        from infrastructure.email.service import email_service

        user = User.objects.get(pk=user_id)

        result = email_service.send_template(
            to=user.email,
            template_name="password_reset",
            context={
                "user": user,
                "verification_code": display_token,
                "subject": "Redefinição de senha",
            },
        )

        if result.success:
            logger.info("Password reset email sent to user=%s", user.public_id)
        else:
            logger.warning(
                "Password reset email failed for user=%s: %s",
                user.public_id,
                result.error,
            )
            raise Exception(f"Email send failed: {result.error}")

    except User.DoesNotExist:
        logger.error("send_password_reset_email: User pk=%s not found", user_id)
    except Exception as exc:
        logger.exception("send_password_reset_email failed for user_id=%s", user_id)
        raise self.retry(exc=exc)


@shared_task(
    name="identity.send_welcome_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_welcome_email_task(self, user_id: int):
    """
    Send welcome email to a newly verified user.

    Args:
        user_id: The database PK of the user.
    """
    try:
        from apps.identity.models import User
        from infrastructure.email.service import email_service

        user = User.objects.get(pk=user_id)

        result = email_service.send_welcome(user)

        if result.success:
            logger.info("Welcome email sent to user=%s", user.public_id)
        else:
            logger.warning(
                "Welcome email failed for user=%s: %s",
                user.public_id,
                result.error,
            )
            raise Exception(f"Email send failed: {result.error}")

    except User.DoesNotExist:
        logger.error("send_welcome_email: User pk=%s not found", user_id)
    except Exception as exc:
        logger.exception("send_welcome_email failed for user_id=%s", user_id)
        raise self.retry(exc=exc)


@shared_task(
    name="identity.cleanup_expired_tokens",
    ignore_result=True,
)
def cleanup_expired_tokens_task():
    """
    Periodic task: Clean up expired and used tokens.

    Delegates to TokenService.cleanup_expired_tokens() which:
    - Deletes expired tokens
    - Deletes used tokens older than 7 days (audit retention)

    Scheduled via celery-beat (see settings).
    """
    from apps.identity.services.token_service import TokenService

    count = TokenService.cleanup_expired_tokens()
    logger.info("Token cleanup: removed %d expired/used tokens", count)
    return count
