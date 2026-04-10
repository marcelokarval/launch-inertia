"""
Notification service layer.

Encapsulates all notification business logic:
- Listing with filtering and pagination
- Read status management
- Creation from raw data or templates
"""

import logging

from django.db import transaction
from django.utils import timezone

from core.shared.services.base import BaseService
from ..models import Notification, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService(BaseService[Notification]):
    """
    Service for managing user notifications.

    Usage:
        service = NotificationService(user=request.user)
        data = service.list_notifications(request.user, status_filter="unread")
        service.mark_as_read(request.user, "ntf_abc123")
    """

    model = Notification

    # ── Read Operations ──────────────────────────────────────────────────

    def list_notifications(
        self,
        user,
        status_filter: str = "all",
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """
        List notifications for a user with filtering and pagination.

        Args:
            user: The recipient user.
            status_filter: "all", "unread", or "read".
            page: 1-based page number.
            per_page: Items per page.

        Returns:
            Dict with keys: items, unread_count, pagination.
        """
        qs = Notification.objects.filter(recipient=user).order_by("-created_at")

        if status_filter == "unread":
            qs = qs.filter(is_read=False)
        elif status_filter == "read":
            qs = qs.filter(is_read=True)

        total = qs.count()
        offset = (page - 1) * per_page
        items = qs[offset : offset + per_page]

        unread_count = Notification.objects.filter(
            recipient=user, is_read=False
        ).count()

        return {
            "items": [n.to_dict() for n in items],
            "unread_count": unread_count,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page if total > 0 else 1,
            },
        }

    def get_unread_count(self, user) -> int:
        """Return the number of unread notifications for a user."""
        return Notification.objects.filter(recipient=user, is_read=False).count()

    # ── Write Operations ─────────────────────────────────────────────────

    def mark_as_read(self, user, public_id: str) -> Notification:
        """
        Mark a single notification as read.

        Args:
            user: The recipient (for ownership verification).
            public_id: The notification's public_id.

        Returns:
            The updated Notification instance.

        Raises:
            Http404: If notification not found or doesn't belong to user.
        """
        from django.http import Http404

        try:
            notification = Notification.objects.get(public_id=public_id, recipient=user)
        except Notification.DoesNotExist:
            raise Http404(f"Notification not found: {public_id}")

        notification.mark_as_read()
        logger.info("Marked notification %s as read for user=%s", public_id, user)
        return notification

    @transaction.atomic
    def mark_all_as_read(self, user) -> int:
        """
        Mark all unread notifications as read for a user.

        Sets both is_read=True AND read_at=now() to maintain
        consistency with the single mark_as_read behavior.

        Args:
            user: The recipient user.

        Returns:
            Number of notifications updated.
        """
        now = timezone.now()
        count = Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True, read_at=now
        )

        logger.info("Marked %d notifications as read for user=%s", count, user)
        return count

    @transaction.atomic
    def create_notification(
        self,
        recipient,
        title: str,
        body: str,
        notification_type: str = "info",
        action_url: str | None = None,
        action_label: str | None = None,
        actor=None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            recipient: The user who will receive the notification.
            title: Notification title.
            body: Notification body text.
            notification_type: One of info, success, warning, error, action.
            action_url: Optional URL for the notification action.
            action_label: Optional label for the action button.
            actor: Optional user who triggered the notification.

        Returns:
            The created Notification instance.
        """
        notification = self.create(
            recipient=recipient,
            title=title,
            body=body,
            notification_type=notification_type,
            action_url=action_url or "",
            action_label=action_label or "",
            actor=actor,
        )
        logger.info(
            "Created notification %s for user=%s (type=%s)",
            notification.public_id,
            recipient,
            notification_type,
        )
        return notification

    @transaction.atomic
    def create_from_template(
        self,
        recipient,
        template_slug: str,
        context: dict,
        notification_type: str = "info",
    ) -> Notification:
        """
        Create a notification by rendering a NotificationTemplate.

        Args:
            recipient: The user who will receive the notification.
            template_slug: Slug of the NotificationTemplate to use.
            context: Dict of variables to render into the template.
            notification_type: One of info, success, warning, error, action.

        Returns:
            The created Notification instance.

        Raises:
            NotificationTemplate.DoesNotExist: If template slug not found.
        """
        template = NotificationTemplate.objects.get(slug=template_slug)
        rendered = template.render(context)

        notification = self.create(
            recipient=recipient,
            title=rendered["title"],
            body=rendered["body"],
            notification_type=notification_type,
            template=template,
        )
        logger.info(
            "Created notification %s from template '%s' for user=%s",
            notification.public_id,
            template_slug,
            recipient,
        )
        return notification
