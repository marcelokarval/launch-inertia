"""
Signal definitions and receivers for the identity app.

Custom signals:
- user_registered: Fired after a new user account is created
- email_verified: Fired after a user's email is verified

Receivers handle side effects like:
- Sending welcome emails (async via Celery)
- Creating welcome notifications
- Logging audit events
"""

import logging

from django.dispatch import Signal, receiver

logger = logging.getLogger(__name__)


# ── Custom Signals ───────────────────────────────────────────────────

# Sent after a new user registers (user=User instance)
user_registered = Signal()

# Sent after a user's email is verified (user=User instance)
email_verified = Signal()


# ── Signal Receivers ─────────────────────────────────────────────────


@receiver(email_verified)
def on_email_verified_send_welcome(sender, user, **kwargs):
    """
    Send a welcome email asynchronously when a user verifies their email.
    """
    from apps.identity.tasks import send_welcome_email_task

    send_welcome_email_task.delay(user_id=user.pk)
    logger.info("Welcome email task queued for user=%s", user.public_id)


@receiver(email_verified)
def on_email_verified_create_notification(sender, user, **kwargs):
    """
    Create a welcome notification when a user verifies their email.
    """
    try:
        from apps.notifications.models import Notification

        Notification.objects.create(
            recipient=user,
            notification_type="success",
            title="Email Verified",
            body="Your email has been verified successfully. Welcome to Launch!",
            action_url="/dashboard/",
        )
    except Exception:
        logger.exception(
            "Failed to create welcome notification for user=%s", user.public_id
        )


@receiver(user_registered)
def on_user_registered_log(sender, user, **kwargs):
    """
    Log user registration events for audit trail.
    """
    logger.info(
        "User registered: public_id=%s email=%s",
        user.public_id,
        user.email,
    )
