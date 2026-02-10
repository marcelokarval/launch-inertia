"""
Celery tasks for the notifications app.

Tasks for:
- Cleaning up old read notifications periodically
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="notifications.cleanup_old_notifications",
    ignore_result=True,
)
def cleanup_old_notifications_task(days: int = 90):
    """
    Periodic task: Delete old read notifications.

    Removes notifications that have been read and are older than `days` days.
    Unread notifications are never deleted automatically.

    Args:
        days: Number of days to retain read notifications (default: 90).
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=days)

    old_notifications = Notification.objects.filter(
        is_read=True,
        read_at__lt=cutoff,
    )
    count = old_notifications.count()

    if count > 0:
        old_notifications.delete()
        logger.info(
            "Notification cleanup: removed %d read notifications older than %d days",
            count,
            days,
        )
    else:
        logger.debug("Notification cleanup: no old read notifications to remove")

    return count
