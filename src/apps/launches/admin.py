"""
Admin configuration for launches app using django-unfold.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.launches.models import CapturePage, Interest, Launch


@admin.register(Interest)
class InterestAdmin(ModelAdmin):
    list_display = ("name", "slug", "default_list_id", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(Launch)
class LaunchAdmin(ModelAdmin):
    list_display = (
        "name",
        "launch_code",
        "status",
        "starts_at",
        "ends_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("name", "launch_code")
    readonly_fields = ("public_id", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "launch_code", "status", "description"),
            },
        ),
        (
            "Dates",
            {
                "fields": ("starts_at", "ends_at"),
            },
        ),
        (
            "Default Config",
            {
                "fields": ("default_config",),
                "classes": ("collapse",),
            },
        ),
        (
            "System",
            {
                "fields": ("public_id", "created_at", "updated_at"),
            },
        ),
    )


@admin.register(CapturePage)
class CapturePageAdmin(ModelAdmin):
    list_display = (
        "slug",
        "name",
        "launch",
        "interest",
        "page_type",
        "layout_type",
        "is_active",
        "created_at",
    )
    list_filter = ("page_type", "layout_type", "launch", "interest", "is_active")
    search_fields = ("slug", "name")
    readonly_fields = ("public_id", "created_at", "updated_at")
    autocomplete_fields = ("launch", "interest")
    fieldsets = (
        (
            None,
            {
                "fields": ("slug", "name", "launch", "interest"),
            },
        ),
        (
            "Type & Layout",
            {
                "fields": ("page_type", "layout_type"),
            },
        ),
        (
            "Page Config (JSON)",
            {
                "fields": ("config",),
                "description": (
                    "Page-specific config. Missing keys fall back to "
                    "Launch.default_config. Keys: meta, headline, subheadline, "
                    "background_image, badges, form, trust_badge, social_proof, "
                    "thank_you, topBanner, etc."
                ),
            },
        ),
        (
            "N8N Integration",
            {
                "fields": ("n8n_webhook_url", "n8n_list_id"),
            },
        ),
        (
            "System",
            {
                "fields": ("public_id", "is_active", "created_at", "updated_at"),
            },
        ),
    )
