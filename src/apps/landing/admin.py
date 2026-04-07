"""Landing admin configuration."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.landing.models import LeadCaptureIdempotencyKey, LeadIntegrationOutbox


@admin.register(LeadIntegrationOutbox)
class LeadIntegrationOutboxAdmin(ModelAdmin):
    """Operational visibility for external lead deliveries."""

    list_display = (
        "public_id",
        "integration_type",
        "status",
        "attempts",
        "capture_submission",
        "identity_public_id",
        "next_retry_at",
        "processed_at",
        "created_at",
    )
    list_filter = (
        "integration_type",
        "status",
        "attempts",
        "created_at",
        "processed_at",
    )
    search_fields = (
        "public_id",
        "identity_public_id",
        "capture_submission__public_id",
        "capture_submission__email_raw",
        "last_error",
    )
    ordering = ("status", "next_retry_at", "-created_at")
    autocomplete_fields = ("capture_submission",)
    readonly_fields = (
        "public_id",
        "capture_token",
        "capture_submission",
        "integration_type",
        "status",
        "payload",
        "response_data",
        "attempts",
        "last_error",
        "identity_public_id",
        "last_attempt_at",
        "next_retry_at",
        "processed_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "public_id",
                    "integration_type",
                    "status",
                    "capture_submission",
                    "capture_token",
                    "identity_public_id",
                )
            },
        ),
        (
            "Delivery",
            {
                "fields": (
                    "attempts",
                    "last_error",
                    "last_attempt_at",
                    "next_retry_at",
                    "processed_at",
                )
            },
        ),
        (
            "Payload",
            {
                "fields": ("payload", "response_data"),
                "classes": ("collapse",),
            },
        ),
        (
            "System",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False


@admin.register(LeadCaptureIdempotencyKey)
class LeadCaptureIdempotencyKeyAdmin(ModelAdmin):
    """Operational visibility for capture submit idempotency records."""

    list_display = (
        "public_id",
        "status",
        "request_id",
        "email_normalized",
        "capture_page",
        "capture_submission",
        "updated_at",
        "created_at",
    )
    list_filter = (
        "status",
        "capture_page",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "public_id",
        "key",
        "request_id",
        "email_normalized",
        "identity__public_id",
        "capture_submission__public_id",
    )
    ordering = ("status", "-updated_at")
    autocomplete_fields = ("capture_page", "capture_submission")
    readonly_fields = (
        "public_id",
        "key",
        "capture_token",
        "request_id",
        "email_normalized",
        "status",
        "capture_page",
        "identity",
        "capture_submission",
        "thank_you_url",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "public_id",
                    "status",
                    "key",
                    "capture_token",
                    "request_id",
                    "email_normalized",
                )
            },
        ),
        (
            "Resolution",
            {
                "fields": (
                    "capture_page",
                    "identity",
                    "capture_submission",
                    "thank_you_url",
                )
            },
        ),
        (
            "System",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False
