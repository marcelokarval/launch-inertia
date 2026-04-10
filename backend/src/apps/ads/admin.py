"""Admin registration for Ads & Traffic models."""

from django.contrib import admin

from apps.ads.models import (
    AdCampaign,
    AdCreative,
    AdGroup,
    AdPlatform,
    AdProvider,
    CaptureSubmission,
    TrafficSource,
)


@admin.register(AdProvider)
class AdProviderAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]


@admin.register(AdPlatform)
class AdPlatformAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "provider"]
    list_filter = ["provider"]
    search_fields = ["code", "name"]


@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    list_display = ["platform", "placement", "created_at"]
    list_filter = ["platform__provider"]
    search_fields = ["placement"]


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "launch", "funnel_stage", "created_at"]
    list_filter = ["provider", "funnel_stage"]
    search_fields = ["name", "provider_id"]
    raw_id_fields = ["launch", "interest"]


@admin.register(AdGroup)
class AdGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "campaign",
        "payment_type",
        "audience_temperature",
        "created_at",
    ]
    list_filter = ["payment_type", "audience_temperature"]
    search_fields = ["name", "provider_id"]
    raw_id_fields = ["campaign"]


@admin.register(AdCreative)
class AdCreativeAdmin(admin.ModelAdmin):
    list_display = [
        "full_code",
        "creative_code",
        "provider",
        "original_interest",
        "funnel_stage",
    ]
    list_filter = ["provider", "funnel_stage"]
    search_fields = ["creative_code", "full_code", "provider_id"]
    raw_id_fields = ["original_interest"]


@admin.register(CaptureSubmission)
class CaptureSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "email_raw",
        "capture_page",
        "n8n_status",
        "is_duplicate",
        "created_at",
    ]
    list_filter = ["n8n_status", "is_duplicate"]
    search_fields = ["email_raw", "phone_raw", "click_id"]
    raw_id_fields = [
        "identity",
        "capture_page",
        "traffic_source",
        "ad_group",
        "ad_creative",
        "device_profile",
    ]
    readonly_fields = ["capture_token", "public_id"]
