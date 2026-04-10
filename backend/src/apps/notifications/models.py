"""
Notifications domain models.

Multi-channel notification system with templates.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from core.shared.models.base import BaseModel


class NotificationTemplate(BaseModel):
    """
    Reusable notification templates.
    """

    PUBLIC_ID_PREFIX = "ntp"

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Template content for different channels
    title_template = models.CharField(max_length=255)
    body_template = models.TextField()

    # Optional channel-specific templates
    email_subject = models.CharField(max_length=255, blank=True)
    email_body = models.TextField(blank=True)
    sms_template = models.CharField(max_length=160, blank=True)
    push_title = models.CharField(max_length=100, blank=True)
    push_body = models.CharField(max_length=255, blank=True)

    # Template variables schema
    variables_schema = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self):
        return self.name

    def render(self, context: dict) -> dict:
        """Render template with context variables."""
        return {
            "title": self.title_template.format(**context),
            "body": self.body_template.format(**context),
        }


class Notification(BaseModel):
    """
    Individual notification instance.
    """

    PUBLIC_ID_PREFIX = "ntf"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # Notification type
    class NotificationType(models.TextChoices):
        INFO = "info", "Information"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        ACTION = "action", "Action Required"

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )

    # Content
    title = models.CharField(max_length=255)
    body = models.TextField()

    # Optional template reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Action URL (optional)
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)

    # Read status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Channel delivery tracking
    channels_sent = models.JSONField(default=list, blank=True)

    # Actor (who triggered the notification)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title[:50]}"

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def to_dict(self) -> dict:
        """Serialize notification for Inertia props."""
        return {
            "id": self.public_id,
            "type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "action_url": self.action_url,
            "action_label": self.action_label,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "actor": self.actor.to_dict() if self.actor else None,
        }

    @classmethod
    def create_for_user(
        cls,
        recipient,
        title: str,
        body: str,
        notification_type: str = "info",
        action_url: str = "",
        action_label: str = "",
        actor=None,
    ) -> "Notification":
        """Helper to create a notification for a user."""
        return cls.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            notification_type=notification_type,
            action_url=action_url,
            action_label=action_label,
            actor=actor,
        )
