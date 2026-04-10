"""Landing domain models."""

from django.db import models

from core.shared.models.base import BaseModel


class LeadCaptureIdempotencyKey(BaseModel):
    """Persistent idempotency boundary for valid capture submits."""

    PUBLIC_ID_PREFIX = "lik"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"

    key = models.CharField(max_length=64, unique=True, db_index=True)
    capture_token = models.UUIDField(db_index=True)
    request_id = models.CharField(max_length=100, blank=True, db_index=True)
    email_normalized = models.CharField(max_length=255, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
        db_index=True,
    )
    capture_page = models.ForeignKey(
        "launches.CapturePage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_keys",
    )
    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_capture_idempotency_keys",
    )
    capture_submission = models.ForeignKey(
        "ads.CaptureSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_keys",
    )
    thank_you_url = models.CharField(max_length=500, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "landing_lead_capture_idempotency"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["capture_token", "email_normalized"]),
            models.Index(fields=["request_id", "email_normalized"]),
        ]

    def __str__(self) -> str:
        return f"{self.key[:12]} ({self.status})"


class LeadIntegrationOutbox(BaseModel):
    """Durable outbox for external lead integration deliveries.

    Stores the payload and delivery lifecycle for integrations triggered by a
    successful capture flow, such as N8N and Meta CAPI.
    """

    PUBLIC_ID_PREFIX = "lio"

    class IntegrationType(models.TextChoices):
        N8N = "n8n", "N8N"
        META_CAPI = "meta_capi", "Meta CAPI"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    capture_submission = models.ForeignKey(
        "ads.CaptureSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integration_outbox_entries",
    )
    capture_token = models.UUIDField(db_index=True)
    integration_type = models.CharField(
        max_length=20,
        choices=IntegrationType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    payload = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    identity_public_id = models.CharField(max_length=32, blank=True, db_index=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "landing_lead_integration_outbox"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["capture_token", "integration_type"],
                name="uniq_lio_capture_token_type",
            )
        ]
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["integration_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.integration_type}:{self.capture_token} ({self.status})"
