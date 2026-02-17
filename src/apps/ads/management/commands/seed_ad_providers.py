"""
Management command to seed AdProvider and AdPlatform reference data.

Usage:
    uv run python manage.py seed_ad_providers
    uv run python manage.py seed_ad_providers --force  # Reset and re-seed
"""

from django.core.management.base import BaseCommand

from apps.ads.models import AdPlatform, AdProvider


# ── Provider definitions ─────────────────────────────────────────────

PROVIDERS: list[dict] = [
    {
        "code": "meta",
        "name": "Meta Ads",
        "api_config": {
            "base_url": "https://graph.facebook.com/v21.0",
            "auth_type": "oauth2",
            "insights_endpoint": "/{id}/insights",
            "rate_limit_per_minute": 200,
            "available_metrics": [
                "spend",
                "impressions",
                "reach",
                "cpm",
                "cpl",
                "ctr",
                "clicks",
            ],
        },
        "source_patterns": {
            "utm_source_patterns": [
                r"Instagram_.*",
                r"Facebook_.*",
                r"ig",
                r"fb",
                r"Audience_Network_.*",
                r"Messenger_.*",
            ],
            "vk_source_values": ["paid_metaads"],
            "click_id_param": "fbclid",
        },
        "naming_convention": {
            "utm_medium_separator": "|",
            "utm_medium_segments": [
                "payment_type",
                "audience_temp",
                "adgroup_name",
                "adgroup_provider_id",
            ],
            "utm_campaign_separator": "|",
            "utm_campaign_segments": [
                "launch_code",
                "campaign_name",
                "campaign_provider_id",
            ],
            "utm_content_separator": "_",
            "utm_content_segments": [
                "creative_seq",
                "interest_code",
                "funnel_stage",
                "creative_launch_code",
            ],
            "ad_id_param": "vk_ad_id",
            "adset_id_fallback": "utm_term",
            "campaign_id_fallback": "utm_id",
        },
    },
    {
        "code": "google",
        "name": "Google Ads",
        "api_config": {
            "base_url": "https://googleads.googleapis.com/v18",
            "auth_type": "oauth2",
            "rate_limit_per_minute": 100,
            "available_metrics": [
                "cost_micros",
                "impressions",
                "clicks",
                "ctr",
                "conversions",
            ],
        },
        "source_patterns": {
            "utm_source_patterns": [r"google", r"Google_.*"],
            "vk_source_values": ["paid_google"],
            "click_id_param": "gclid",
        },
        "naming_convention": {
            "utm_medium_separator": "|",
            "utm_medium_segments": ["payment_type", "match_type", "adgroup_name"],
            "utm_campaign_separator": "|",
            "utm_campaign_segments": ["launch_code", "campaign_name"],
            "utm_content_separator": "_",
            "utm_content_segments": ["creative_seq", "variant"],
        },
    },
    {
        "code": "tiktok",
        "name": "TikTok Ads",
        "api_config": {
            "base_url": "https://business-api.tiktok.com/open_api/v1.3",
            "auth_type": "access_token",
            "rate_limit_per_minute": 60,
            "available_metrics": [
                "spend",
                "impressions",
                "clicks",
                "reach",
                "ctr",
            ],
        },
        "source_patterns": {
            "utm_source_patterns": [r"tiktok", r"TikTok_.*"],
            "vk_source_values": ["paid_tiktok"],
            "click_id_param": "ttclid",
        },
        "naming_convention": {
            "utm_medium_separator": "|",
            "utm_medium_segments": ["payment_type", "audience_temp", "adgroup_name"],
            "utm_campaign_separator": "|",
            "utm_campaign_segments": ["launch_code", "campaign_name"],
            "utm_content_separator": "_",
            "utm_content_segments": ["creative_seq", "interest_code", "funnel_stage"],
        },
    },
    {
        "code": "organic",
        "name": "Organico",
        "api_config": {},
        "source_patterns": {
            "utm_source_patterns": [],
            "vk_source_values": [],
            "click_id_param": "",
        },
        "naming_convention": {},
    },
    {
        "code": "direct",
        "name": "Direto",
        "api_config": {},
        "source_patterns": {
            "utm_source_patterns": [],
            "vk_source_values": [],
            "click_id_param": "",
        },
        "naming_convention": {},
    },
]


# ── Platform definitions ─────────────────────────────────────────────

PLATFORMS: list[dict] = [
    # Meta platforms
    {
        "provider_code": "meta",
        "code": "instagram",
        "name": "Instagram",
        "platform_data": {
            "icon_url": "/static/icons/instagram.svg",
            "valid_placements": [
                "reels",
                "feed",
                "stories",
                "explore",
                "shop",
            ],
            "default_placement": "feed",
        },
    },
    {
        "provider_code": "meta",
        "code": "facebook",
        "name": "Facebook",
        "platform_data": {
            "icon_url": "/static/icons/facebook.svg",
            "valid_placements": [
                "feed",
                "stories",
                "reels",
                "marketplace",
                "video_feeds",
                "right_column",
                "instant_articles",
            ],
            "default_placement": "feed",
        },
    },
    {
        "provider_code": "meta",
        "code": "messenger",
        "name": "Messenger",
        "platform_data": {
            "icon_url": "/static/icons/messenger.svg",
            "valid_placements": ["inbox", "stories", "sponsored_messages"],
            "default_placement": "inbox",
        },
    },
    {
        "provider_code": "meta",
        "code": "audience_network",
        "name": "Audience Network",
        "platform_data": {
            "valid_placements": ["native", "banner", "interstitial", "rewarded_video"],
            "default_placement": "native",
        },
    },
    # Google platforms
    {
        "provider_code": "google",
        "code": "google_search",
        "name": "Google Search",
        "platform_data": {
            "icon_url": "/static/icons/google.svg",
            "valid_placements": ["search_results", "shopping"],
            "default_placement": "search_results",
        },
    },
    {
        "provider_code": "google",
        "code": "google_display",
        "name": "Google Display",
        "platform_data": {
            "valid_placements": ["display", "gmail"],
            "default_placement": "display",
        },
    },
    {
        "provider_code": "google",
        "code": "youtube",
        "name": "YouTube",
        "platform_data": {
            "icon_url": "/static/icons/youtube.svg",
            "valid_placements": [
                "in_stream",
                "in_feed",
                "shorts",
                "bumper",
                "discovery",
            ],
            "default_placement": "in_stream",
        },
    },
    # TikTok platform
    {
        "provider_code": "tiktok",
        "code": "tiktok",
        "name": "TikTok",
        "platform_data": {
            "icon_url": "/static/icons/tiktok.svg",
            "valid_placements": ["for_you", "search", "profile"],
            "default_placement": "for_you",
        },
    },
    # Organic "platforms" (represent traffic sources without ads)
    {
        "provider_code": "organic",
        "code": "ig",
        "name": "Instagram (Organico)",
        "platform_data": {
            "valid_placements": ["link_in_bio", "stories", "dms", "post"],
            "default_placement": "link_in_bio",
        },
    },
    {
        "provider_code": "organic",
        "code": "whatsapp",
        "name": "WhatsApp",
        "platform_data": {
            "valid_placements": ["direct", "group", "broadcast"],
            "default_placement": "direct",
        },
    },
    {
        "provider_code": "organic",
        "code": "email_organic",
        "name": "Email (Organico)",
        "platform_data": {
            "valid_placements": ["newsletter", "transactional"],
            "default_placement": "newsletter",
        },
    },
    # Direct
    {
        "provider_code": "direct",
        "code": "direct",
        "name": "Acesso Direto",
        "platform_data": {
            "valid_placements": ["direct"],
            "default_placement": "direct",
        },
    },
]


class Command(BaseCommand):
    help = "Seed AdProvider and AdPlatform reference data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing data and re-seed from scratch.",
        )

    def handle(self, *args, **options):
        force = options["force"]

        if force:
            self.stdout.write("Deleting existing platforms and providers...")
            AdPlatform.objects.all().delete()
            AdProvider.objects.all().delete()

        # Seed providers
        providers_created = 0
        providers_updated = 0
        for pdata in PROVIDERS:
            obj, created = AdProvider.objects.update_or_create(
                code=pdata["code"],
                defaults={
                    "name": pdata["name"],
                    "api_config": pdata.get("api_config", {}),
                    "source_patterns": pdata.get("source_patterns", {}),
                    "naming_convention": pdata.get("naming_convention", {}),
                },
            )
            if created:
                providers_created += 1
            else:
                providers_updated += 1

        self.stdout.write(
            f"AdProvider: {providers_created} created, {providers_updated} updated."
        )

        # Seed platforms
        platforms_created = 0
        platforms_updated = 0
        for pldata in PLATFORMS:
            provider = AdProvider.objects.get(code=pldata["provider_code"])
            obj, created = AdPlatform.objects.update_or_create(
                code=pldata["code"],
                defaults={
                    "provider": provider,
                    "name": pldata["name"],
                    "platform_data": pldata.get("platform_data", {}),
                },
            )
            if created:
                platforms_created += 1
            else:
                platforms_updated += 1

        self.stdout.write(
            f"AdPlatform: {platforms_created} created, {platforms_updated} updated."
        )

        total = providers_created + platforms_created
        self.stdout.write(
            self.style.SUCCESS(f"Seed complete: {total} records created.")
        )
