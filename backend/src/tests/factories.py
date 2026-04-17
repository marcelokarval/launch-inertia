# pyright: reportPrivateImportUsage=false
"""
Model factories for tests.

Uses factory_boy to create test instances of all major models.
"""

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = "identity.User"
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    email_verified = True
    status = "active"

    class Params:
        """Trait params for common variations."""

        unverified = factory.Trait(
            email_verified=False,
            status="pending",
        )
        staff = factory.Trait(
            is_staff=True,
        )
        superuser = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )
        locked = factory.Trait(
            status="locked",
            failed_login_attempts=5,
        )


class ProfileFactory(DjangoModelFactory):
    """Factory for creating Profile instances."""

    class Meta:
        model = "identity.Profile"

    user = factory.SubFactory(UserFactory)
    phone = factory.Faker("phone_number")
    bio = factory.Faker("sentence")
    agreed_to_terms = True


class IdentityFactory(DjangoModelFactory):
    """Factory for creating Identity instances."""

    class Meta:
        model = "contact_identity.Identity"

    status = "active"
    confidence_score = factory.Faker("pyfloat", min_value=0.0, max_value=1.0)
    display_name = factory.Faker("name")
    first_seen_source = "manual"


class ContactEmailFactory(DjangoModelFactory):
    """Factory for creating ContactEmail instances."""

    class Meta:
        model = "contact_email.ContactEmail"

    value = factory.Sequence(lambda n: f"contact{n}@example.com")
    identity = factory.SubFactory(IdentityFactory)
    is_verified = False
    lifecycle_status = "pending"


class ContactPhoneFactory(DjangoModelFactory):
    """Factory for creating ContactPhone instances."""

    class Meta:
        model = "contact_phone.ContactPhone"

    value = factory.Sequence(lambda n: f"+5511999{n:06d}")
    identity = factory.SubFactory(IdentityFactory)
    is_verified = False
    is_whatsapp = False


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances."""

    class Meta:
        model = "contacts.Tag"

    name = factory.Sequence(lambda n: f"Tag {n}")
    color = factory.Faker("hex_color")


class NotificationFactory(DjangoModelFactory):
    """Factory for creating Notification instances."""

    class Meta:
        model = "notifications.Notification"

    recipient = factory.SubFactory(UserFactory)
    notification_type = "info"
    title = factory.Faker("sentence", nb_words=4)
    body = factory.Faker("paragraph")
    is_read = False


# ── Launches Factories ───────────────────────────────────────────────


class InterestFactory(DjangoModelFactory):
    """Factory for creating Interest instances."""

    class Meta:
        model = "launches.Interest"
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Interest {n}")
    slug = factory.Sequence(lambda n: f"interest-{n}")
    description = factory.Faker("sentence")
    default_list_id = factory.Sequence(lambda n: f"list_{n}")
    default_thank_you_path = factory.LazyAttribute(lambda o: f"/obrigado-{o.slug}/")


class LaunchFactory(DjangoModelFactory):
    """Factory for creating Launch instances."""

    class Meta:
        model = "launches.Launch"
        django_get_or_create = ("launch_code",)

    name = factory.Sequence(lambda n: f"Launch {n}")
    launch_code = factory.Sequence(lambda n: f"WH{n:04d}")
    status = "active"
    description = factory.Faker("sentence")
    default_config = factory.LazyFunction(
        lambda: {
            "highlight_color": "#FB061A",
            "background_image": "/static/images/bg-default.jpg",
            "n8n": {
                "webhook_url": "https://n8n.example.com/webhook/default",
                "launch_code": "WH0001",
                "list_id": "default_list",
            },
        }
    )


class CapturePageFactory(DjangoModelFactory):
    """Factory for creating CapturePage instances."""

    class Meta:
        model = "launches.CapturePage"
        django_get_or_create = ("slug",)

    launch = factory.SubFactory(LaunchFactory)
    interest = factory.SubFactory(InterestFactory)
    slug = factory.Sequence(lambda n: f"wh-page-{n}")
    name = factory.Sequence(lambda n: f"Capture Page {n}")
    page_type = "capture"
    layout_type = "standard"
    config = factory.LazyFunction(
        lambda: {
            "meta": {"title": "Test Page", "description": "Test description"},
            "headline": {
                "parts": [
                    {"text": "Test", "type": "normal"},
                    {"text": " Page", "type": "highlight", "color": "red"},
                ]
            },
            "form": {
                "button_text": "INSCREVER!",
                "button_gradient": "bg-gradient-to-r from-[#0e036b] to-[#fb061a]",
                "thank_you_url": "/obrigado-test/",
            },
            "trust_badge": {"enabled": True, "text": "Seguro", "icon": "shield"},
            "social_proof": {"enabled": False},
        }
    )
    n8n_webhook_url = ""
    n8n_list_id = ""


# ── Ads Factories ─────────────────────────────────────────────────────


class AdProviderFactory(DjangoModelFactory):
    """Factory for creating AdProvider instances (reference table, natural PK)."""

    class Meta:
        model = "ads.AdProvider"
        django_get_or_create = ("code",)

    code = factory.Sequence(lambda n: f"provider_{n}")
    name = factory.LazyAttribute(lambda o: o.code.replace("_", " ").title())
    api_config = factory.LazyFunction(dict)
    source_patterns = factory.LazyFunction(dict)
    naming_convention = factory.LazyFunction(dict)

    class Params:
        """Trait params for common providers."""

        meta = factory.Trait(
            code="meta",
            name="Meta Ads",
            source_patterns={
                "utm_source_patterns": [
                    r"Instagram_.*",
                    r"Facebook_.*",
                    r"ig",
                    r"fb",
                ],
                "vk_source_values": ["paid_metaads"],
                "click_id_param": "fbclid",
            },
            naming_convention={
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
                "adset_id_fallback": "utm_term",
            },
        )
        organic = factory.Trait(
            code="organic",
            name="Organic",
        )
        direct = factory.Trait(
            code="direct",
            name="Direct",
        )


class AdPlatformFactory(DjangoModelFactory):
    """Factory for creating AdPlatform instances."""

    class Meta:
        model = "ads.AdPlatform"
        django_get_or_create = ("code",)

    provider = factory.SubFactory(AdProviderFactory)
    code = factory.Sequence(lambda n: f"platform_{n}")
    name = factory.LazyAttribute(lambda o: o.code.replace("_", " ").title())
    platform_data = factory.LazyFunction(dict)

    class Params:
        """Trait params for common platforms."""

        instagram = factory.Trait(
            code="instagram",
            name="Instagram",
            provider=factory.SubFactory(AdProviderFactory, meta=True),
            platform_data={
                "valid_placements": ["reels", "feed", "stories"],
                "default_placement": "feed",
            },
        )


class TrafficSourceFactory(DjangoModelFactory):
    """Factory for creating TrafficSource instances."""

    class Meta:
        model = "ads.TrafficSource"

    platform = factory.SubFactory(AdPlatformFactory)
    placement = "feed"


class AdCampaignFactory(DjangoModelFactory):
    """Factory for creating AdCampaign instances."""

    class Meta:
        model = "ads.AdCampaign"

    provider = factory.SubFactory(AdProviderFactory)
    external_id = factory.Sequence(lambda n: f"campaign_{n}")
    name = factory.Sequence(lambda n: f"Test Campaign {n}")
    funnel_stage = "capture"
    parsed_data = factory.LazyFunction(dict)
    api_data = factory.LazyFunction(dict)


class AdGroupFactory(DjangoModelFactory):
    """Factory for creating AdGroup instances."""

    class Meta:
        model = "ads.AdGroup"

    campaign = factory.SubFactory(AdCampaignFactory)
    external_id = factory.Sequence(lambda n: f"adset_{n}")
    name = factory.Sequence(lambda n: f"Test Adset {n}")
    payment_type = "paid"
    audience_temperature = "hot"
    parsed_data = factory.LazyFunction(dict)
    api_data = factory.LazyFunction(dict)


class AdCreativeFactory(DjangoModelFactory):
    """Factory for creating AdCreative instances."""

    class Meta:
        model = "ads.AdCreative"

    provider = factory.SubFactory(AdProviderFactory)
    external_id = factory.Sequence(lambda n: f"ad_{n}")
    creative_code = factory.Sequence(lambda n: f"AD{n:03d}")
    full_code = factory.Sequence(lambda n: f"AD{n:03d}_RC_CAPT_WH0126")
    funnel_stage = "capture"
    provider_data = factory.LazyFunction(dict)


class CaptureSubmissionFactory(DjangoModelFactory):
    """Factory for creating CaptureSubmission instances (fact table)."""

    class Meta:
        model = "ads.CaptureSubmission"

    identity = factory.SubFactory(IdentityFactory)
    email_raw = factory.Sequence(lambda n: f"lead{n}@example.com")
    phone_raw = factory.Sequence(lambda n: f"+5511999{n:06d}")
    capture_page = factory.SubFactory(CapturePageFactory)
    capture_token = factory.LazyFunction(lambda: __import__("uuid").uuid4())
    n8n_status = "pending"
    is_duplicate = False
    raw_utm_data = factory.LazyFunction(dict)
