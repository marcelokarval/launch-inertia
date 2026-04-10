"""
Tests for the ads app: models, UTMParserService, seed command, and integration.

Covers:
- AdProvider, AdPlatform reference table creation
- TrafficSource, AdCampaign, AdGroup, AdCreative dimension get_or_create
- CaptureSubmission fact table
- UTMParserService with real production URL patterns
- Seed management command
"""
# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

import uuid

import pytest

from apps.ads.models import (
    AdCampaign,
    AdCreative,
    AdGroup,
    AdPlatform,
    AdProvider,
    CaptureSubmission,
    TrafficSource,
)
from apps.ads.services.utm_parser import ParsedUTMResult, UTMParserService
from tests.factories import (
    CapturePageFactory,
    IdentityFactory,
    InterestFactory,
    LaunchFactory,
)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def meta_provider(db):
    """Create Meta Ads provider with full naming convention."""
    return AdProvider.objects.create(
        code="meta",
        name="Meta Ads",
        source_patterns={
            "utm_source_patterns": [r"Instagram_.*", r"Facebook_.*", r"ig", r"fb"],
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
            "ad_id_param": "vk_ad_id",
            "adset_id_fallback": "utm_term",
            "campaign_id_fallback": "utm_id",
        },
    )


@pytest.fixture
def organic_provider(db):
    return AdProvider.objects.create(
        code="organic",
        name="Organico",
        source_patterns={
            "utm_source_patterns": [],
            "vk_source_values": [],
            "click_id_param": "",
        },
        naming_convention={},
    )


@pytest.fixture
def direct_provider(db):
    return AdProvider.objects.create(
        code="direct",
        name="Direto",
        source_patterns={
            "utm_source_patterns": [],
            "vk_source_values": [],
            "click_id_param": "",
        },
        naming_convention={},
    )


@pytest.fixture
def instagram_platform(meta_provider):
    return AdPlatform.objects.create(
        provider=meta_provider,
        code="instagram",
        name="Instagram",
        platform_data={
            "valid_placements": ["reels", "feed", "stories", "explore"],
            "default_placement": "feed",
        },
    )


@pytest.fixture
def facebook_platform(meta_provider):
    return AdPlatform.objects.create(
        provider=meta_provider,
        code="facebook",
        name="Facebook",
        platform_data={
            "valid_placements": ["feed", "stories", "reels", "marketplace"],
            "default_placement": "feed",
        },
    )


@pytest.fixture
def all_providers(meta_provider, organic_provider, direct_provider):
    """Ensure all providers exist."""
    return meta_provider, organic_provider, direct_provider


# ── Reference Table Tests ────────────────────────────────────────────


@pytest.mark.django_db
class TestAdProvider:
    def test_create_provider(self):
        provider = AdProvider.objects.create(
            code="test",
            name="Test Provider",
            api_config={"base_url": "https://api.test.com"},
        )
        assert provider.code == "test"
        assert provider.name == "Test Provider"
        assert provider.api_config["base_url"] == "https://api.test.com"

    def test_natural_pk(self):
        """AdProvider uses code as PK, not auto-generated."""
        provider = AdProvider.objects.create(code="pk_test", name="PK Test")
        assert provider.pk == "pk_test"

    def test_str(self):
        provider = AdProvider.objects.create(code="str_test", name="String Test")
        assert str(provider) == "String Test"


@pytest.mark.django_db
class TestAdPlatform:
    def test_create_platform(self, meta_provider):
        platform = AdPlatform.objects.create(
            provider=meta_provider,
            code="test_platform",
            name="Test Platform",
        )
        assert platform.provider == meta_provider
        assert platform.code == "test_platform"

    def test_unique_code(self, meta_provider):
        AdPlatform.objects.create(provider=meta_provider, code="unique_code", name="A")
        with pytest.raises(Exception):
            AdPlatform.objects.create(
                provider=meta_provider, code="unique_code", name="B"
            )

    def test_str(self, instagram_platform):
        assert "Instagram" in str(instagram_platform)
        assert "meta" in str(instagram_platform)


# ── Dimension Table Tests ────────────────────────────────────────────


@pytest.mark.django_db
class TestTrafficSource:
    def test_get_or_create(self, instagram_platform):
        source, created = TrafficSource.objects.get_or_create(
            platform=instagram_platform,
            placement="reels",
        )
        assert created
        assert source.placement == "reels"
        assert source.platform.code == "instagram"

        # Second call: same row
        source2, created2 = TrafficSource.objects.get_or_create(
            platform=instagram_platform,
            placement="reels",
        )
        assert not created2
        assert source.pk == source2.pk

    def test_public_id_prefix(self, instagram_platform):
        source = TrafficSource.objects.create(
            platform=instagram_platform,
            placement="stories",
        )
        assert source.public_id.startswith("tfs_")

    def test_unique_together(self, instagram_platform):
        TrafficSource.objects.create(
            platform=instagram_platform,
            placement="feed",
        )
        with pytest.raises(Exception):
            TrafficSource.objects.create(
                platform=instagram_platform,
                placement="feed",
            )


@pytest.mark.django_db
class TestAdCampaign:
    def test_create_paid_campaign(self, meta_provider):
        campaign = AdCampaign.objects.create(
            provider=meta_provider,
            external_id="120237085838390543",
            name="[WH0126] [Captacao] [Quente] [Repasse] [V1] - Melhores 2",
            funnel_stage="capture",
        )
        assert campaign.external_id == "120237085838390543"
        assert campaign.public_id.startswith("acp_")

    def test_create_organic_campaign(self, meta_provider):
        campaign = AdCampaign.objects.create(
            provider=meta_provider,
            external_id="",
            name="Organic campaign",
        )
        assert campaign.external_id == ""

    def test_str(self, meta_provider):
        campaign = AdCampaign.objects.create(
            provider=meta_provider,
            name="Test Campaign Name",
        )
        assert "Test Campaign" in str(campaign)


@pytest.mark.django_db
class TestAdGroup:
    def test_create_with_filters(self, meta_provider):
        campaign = AdCampaign.objects.create(
            provider=meta_provider,
            external_id="camp_123",
            name="Test Campaign",
        )
        group = AdGroup.objects.create(
            campaign=campaign,
            external_id="adset_456",
            name="01 - [Mix Quente] [AD364_RC_CAPT_WH0725]",
            payment_type="paid",
            audience_temperature="hot",
        )
        assert group.payment_type == "paid"
        assert group.audience_temperature == "hot"
        assert group.public_id.startswith("agr_")

    def test_filter_by_payment_type(self, meta_provider):
        campaign = AdCampaign.objects.create(provider=meta_provider, name="C1")
        AdGroup.objects.create(
            campaign=campaign, name="Paid Group", payment_type="paid"
        )
        AdGroup.objects.create(
            campaign=campaign, name="Organic Group", payment_type="organic"
        )
        assert AdGroup.objects.filter(payment_type="paid").count() == 1
        assert AdGroup.objects.filter(payment_type="organic").count() == 1


@pytest.mark.django_db
class TestAdCreative:
    def test_create_with_full_code(self, meta_provider):
        creative = AdCreative.objects.create(
            provider=meta_provider,
            external_id="120237085839820543",
            creative_code="AD364",
            full_code="AD364_RC_CAPT_WH0725",
            original_launch_code="WH0725",
            funnel_stage="capture",
        )
        assert creative.creative_code == "AD364"
        assert creative.public_id.startswith("acr_")

    def test_str(self, meta_provider):
        creative = AdCreative.objects.create(
            provider=meta_provider,
            full_code="AD338_TD_CAPT_WH0624",
        )
        assert "AD338" in str(creative)


# ── CaptureSubmission Tests ──────────────────────────────────────────


@pytest.mark.django_db
class TestCaptureSubmission:
    def test_create_full_submission(self, meta_provider, instagram_platform):
        identity = IdentityFactory()
        capture_page = CapturePageFactory()
        campaign = AdCampaign.objects.create(provider=meta_provider, name="Test")
        group = AdGroup.objects.create(
            campaign=campaign, name="Group", payment_type="paid"
        )
        creative = AdCreative.objects.create(
            provider=meta_provider, full_code="AD001_RC_CAPT_WH0126"
        )
        source = TrafficSource.objects.create(
            platform=instagram_platform, placement="reels"
        )

        submission = CaptureSubmission.objects.create(
            identity=identity,
            email_raw="test@example.com",
            phone_raw="+5511999888777",
            capture_page=capture_page,
            traffic_source=source,
            ad_group=group,
            ad_creative=creative,
            click_id="PAZXh0bgTest123",
            capture_token=uuid.uuid4(),
            n8n_status="pending",
        )
        assert submission.public_id.startswith("csb_")
        assert submission.email_raw == "test@example.com"
        assert submission.n8n_status == "pending"

    def test_create_minimal_submission(self):
        identity = IdentityFactory()
        capture_page = CapturePageFactory()
        submission = CaptureSubmission.objects.create(
            identity=identity,
            email_raw="min@test.com",
            phone_raw="11999887766",
            capture_page=capture_page,
            capture_token=uuid.uuid4(),
        )
        assert submission.traffic_source is None
        assert submission.ad_group is None
        assert submission.ad_creative is None

    def test_duplicate_flag(self):
        identity = IdentityFactory()
        capture_page = CapturePageFactory()
        sub1 = CaptureSubmission.objects.create(
            identity=identity,
            email_raw="dup@test.com",
            phone_raw="11999000111",
            capture_page=capture_page,
            capture_token=uuid.uuid4(),
        )
        sub2 = CaptureSubmission.objects.create(
            identity=identity,
            email_raw="dup@test.com",
            phone_raw="11999000111",
            capture_page=capture_page,
            capture_token=uuid.uuid4(),
            is_duplicate=True,
        )
        assert not sub1.is_duplicate
        assert sub2.is_duplicate


# ── UTMParserService Tests ───────────────────────────────────────────


@pytest.mark.django_db
class TestUTMParserService:
    """Test UTM parsing with real production URL patterns."""

    def test_detect_meta_by_utm_source(self, all_providers, instagram_platform):
        """Meta detected from Instagram_Reels utm_source."""
        result = UTMParserService.parse(
            {"utm_source": "Instagram_Reels"},
            {},
        )
        assert result.provider is not None
        assert result.provider.code == "meta"

    def test_detect_meta_by_vk_source(self, all_providers):
        """Meta detected from vk_source=paid_metaads."""
        result = UTMParserService.parse(
            {"utm_source": ""},
            {"vk_source": "paid_metaads"},
        )
        assert result.provider is not None
        assert result.provider.code == "meta"

    def test_detect_meta_by_fbclid(self, all_providers):
        """Meta detected by presence of fbclid."""
        result = UTMParserService.parse(
            {"utm_source": ""},
            {"fbclid": "PAZXh0bgTestFBCLID123"},
        )
        assert result.provider is not None
        assert result.provider.code == "meta"

    def test_detect_direct_no_params(self, all_providers):
        """Direct traffic when no UTM params."""
        result = UTMParserService.parse({}, {})
        assert result.provider is not None
        assert result.provider.code == "direct"

    def test_detect_organic_with_source(self, all_providers):
        """Organic when utm_source exists but doesn't match any provider."""
        result = UTMParserService.parse(
            {"utm_source": "random_blog"},
            {},
        )
        assert result.provider is not None
        assert result.provider.code == "organic"

    def test_parse_full_meta_utm(self, all_providers, instagram_platform):
        """Full Meta Ads URL pattern — real production data."""
        utm_data = {
            "utm_source": "Instagram_Reels",
            "utm_medium": "Pago|Quente|01 - [Mix Quente] [AD364_RC_CAPT_WH0725]|120237085840210543",
            "utm_campaign": "WH0126|[WH0126] [Captacao] [Quente] [Repasse] [V1] - Melhores 2|120237085838390543",
            "utm_content": "AD364_RC_CAPT_WH0725",
            "utm_term": "120237085840210543",
            "utm_id": "120237085838390543",
        }
        extra_params = {
            "vk_ad_id": "120237085839820543",
            "vk_source": "paid_metaads",
            "fbclid": "PAZXh0bgTest_FBCLID_VALUE",
        }

        result = UTMParserService.parse(utm_data, extra_params)

        # Provider
        assert result.provider.code == "meta"

        # Click ID
        assert result.click_id == "PAZXh0bgTest_FBCLID_VALUE"

        # Traffic source
        assert result.traffic_source is not None
        assert result.traffic_source.platform.code == "instagram"
        assert result.traffic_source.placement == "reels"

        # Campaign
        assert result.campaign is not None
        assert result.campaign.external_id == "120237085838390543"
        assert "WH0126" in result.campaign.name

        # Ad group
        assert result.ad_group is not None
        assert result.ad_group.external_id == "120237085840210543"
        assert result.ad_group.payment_type == "paid"
        assert result.ad_group.audience_temperature == "hot"

        # Creative
        assert result.creative is not None
        assert result.creative.external_id == "120237085839820543"
        assert result.creative.full_code == "AD364_RC_CAPT_WH0725"
        assert result.creative.creative_code == "AD364"
        assert result.creative.funnel_stage == "capture"

    def test_parse_idempotent(self, all_providers, instagram_platform):
        """Parsing same UTMs twice returns same dimension rows."""
        utm_data = {
            "utm_source": "Instagram_Feed",
            "utm_medium": "Pago|Frio|Adset Test|999",
            "utm_campaign": "WH0001|Test Campaign|888",
            "utm_content": "AD001_RC_CAPT_WH0001",
        }

        result1 = UTMParserService.parse(utm_data)
        result2 = UTMParserService.parse(utm_data)

        assert result1.traffic_source.pk == result2.traffic_source.pk
        assert result1.campaign.pk == result2.campaign.pk
        assert result1.ad_group.pk == result2.ad_group.pk
        assert result1.creative.pk == result2.creative.pk

        # Verify only 1 row each
        assert TrafficSource.objects.count() == 1
        assert AdCampaign.objects.count() == 1
        assert AdGroup.objects.count() == 1
        assert AdCreative.objects.count() == 1

    def test_parse_with_launch_fk(self, all_providers, instagram_platform):
        """Campaign resolves launch FK from launch_code."""
        launch = LaunchFactory(launch_code="WH0126")
        utm_data = {
            "utm_source": "Facebook_Feed",
            "utm_campaign": "WH0126|Test Campaign|777",
        }

        result = UTMParserService.parse(utm_data)
        assert result.campaign is not None
        assert result.campaign.launch == launch

    def test_parse_missing_campaign(self, all_providers, instagram_platform):
        """No utm_campaign -> campaign is None."""
        result = UTMParserService.parse(
            {"utm_source": "Instagram_Reels"},
        )
        assert result.campaign is None

    def test_split_with_fallback_success(self):
        result = UTMParserService._split_with_fallback(
            "Pago|Quente|Name|123",
            "|",
            ["type", "temp", "name", "id"],
        )
        assert result["type"] == "Pago"
        assert result["temp"] == "Quente"
        assert result["name"] == "Name"
        assert result["id"] == "123"

    def test_split_with_fallback_too_few(self):
        result = UTMParserService._split_with_fallback(
            "Pago|Quente",
            "|",
            ["type", "temp", "name", "id"],
        )
        assert "_raw" in result
        assert "_parse_error" in result

    def test_split_with_fallback_no_separator(self):
        result = UTMParserService._split_with_fallback(
            "simple_value",
            "|",
            ["type", "temp"],
        )
        assert result == {"_raw": "simple_value"}

    def test_split_with_extra_segments(self):
        result = UTMParserService._split_with_fallback(
            "a|b|c|d|e",
            "|",
            ["first", "second"],
        )
        assert result["first"] == "a"
        assert result["second"] == "b"
        assert result["_extra_segments"] == ["c", "d", "e"]


# ── Seed Command Tests ───────────────────────────────────────────────


@pytest.mark.django_db
class TestSeedCommand:
    def test_seed_creates_providers(self):
        from django.core.management import call_command

        call_command("seed_ad_providers")
        assert AdProvider.objects.count() >= 5
        assert AdProvider.objects.filter(code="meta").exists()
        assert AdProvider.objects.filter(code="google").exists()
        assert AdProvider.objects.filter(code="tiktok").exists()
        assert AdProvider.objects.filter(code="organic").exists()
        assert AdProvider.objects.filter(code="direct").exists()

    def test_seed_creates_platforms(self):
        from django.core.management import call_command

        call_command("seed_ad_providers")
        assert AdPlatform.objects.count() >= 10
        assert AdPlatform.objects.filter(code="instagram").exists()
        assert AdPlatform.objects.filter(code="facebook").exists()
        assert AdPlatform.objects.filter(code="youtube").exists()
        assert AdPlatform.objects.filter(code="tiktok").exists()

    def test_seed_idempotent(self):
        from django.core.management import call_command

        call_command("seed_ad_providers")
        count1 = AdProvider.objects.count()
        call_command("seed_ad_providers")
        count2 = AdProvider.objects.count()
        assert count1 == count2

    def test_seed_force(self):
        from django.core.management import call_command

        call_command("seed_ad_providers")
        call_command("seed_ad_providers", force=True)
        assert AdProvider.objects.filter(code="meta").exists()

    def test_meta_naming_convention(self):
        from django.core.management import call_command

        call_command("seed_ad_providers")
        meta = AdProvider.objects.get(code="meta")
        nc = meta.naming_convention
        assert nc["utm_medium_separator"] == "|"
        assert "payment_type" in nc["utm_medium_segments"]
        assert nc["utm_content_separator"] == "_"


# ── Integration: CaptureSubmission creation via views ─────────────────


@pytest.mark.django_db
class TestCaptureSubmissionIntegration:
    """Test the full capture→submission flow via _create_capture_submission."""

    @pytest.fixture(autouse=True)
    def setup_providers(self, all_providers, instagram_platform):
        """Ensure ad providers and platforms exist for each test."""
        self.meta_provider = all_providers[0]  # meta_provider

    def test_create_submission_with_full_utms(self):
        """Full Meta UTM data creates CaptureSubmission with all dimension FKs."""
        from apps.landing.views import _create_capture_submission

        identity = IdentityFactory()
        launch = LaunchFactory(launch_code="WH0126")
        interest = InterestFactory(slug="rc", name="Repasse")
        page = CapturePageFactory(slug="wh-rc-v3", launch=launch, interest=interest)

        utm_data = {
            "utm_source": "Instagram_Reels",
            "utm_medium": "Pago|Quente|01 - [Mix Quente]|120237085840210543",
            "utm_campaign": "WH0126|[WH0126] [Captacao] [Repasse]|120237085838390543",
            "utm_content": "AD364_RC_CAPT_WH0725",
            "utm_term": "120237085840210543",
            "utm_id": "120237085838390543",
        }
        extra_ad_params = {
            "fbclid": "PAZXh0bgTestFBCLID123",
            "vk_ad_id": "120237085839820543",
            "vk_source": "paid_metaads",
        }

        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.post("/inscrever-wh-rc-v3/")
        request.client_ip = "187.100.42.1"
        request.geo_data = {"country": "BR", "city": "Sao Paulo"}
        request.device_data = None
        request.device_profile = None

        import time

        t_start = time.monotonic()

        submission = _create_capture_submission(
            identity=identity,
            email_raw="Lead@Example.com",
            phone_raw="+55 11 99988-7766",
            capture_page=page,
            utm_data=utm_data,
            extra_ad_params=extra_ad_params,
            capture_token=str(uuid.uuid4()),
            visitor_id="fp_test_abc123",
            request=request,
            t_start=t_start,
        )

        assert submission is not None
        assert submission.public_id.startswith("csb_")
        assert submission.identity == identity
        assert submission.email_raw == "Lead@Example.com"
        assert submission.phone_raw == "+55 11 99988-7766"
        assert submission.capture_page == page

        # Traffic source resolved
        assert submission.traffic_source is not None
        assert submission.traffic_source.platform.code == "instagram"
        assert submission.traffic_source.placement == "reels"

        # Ad group resolved
        assert submission.ad_group is not None
        assert submission.ad_group.payment_type == "paid"
        assert submission.ad_group.audience_temperature == "hot"

        # Creative resolved
        assert submission.ad_creative is not None
        assert submission.ad_creative.creative_code == "AD364"
        assert submission.ad_creative.external_id == "120237085839820543"

        # Click ID from fbclid
        assert submission.click_id == "PAZXh0bgTestFBCLID123"

        # Metadata
        assert submission.visitor_id == "fp_test_abc123"
        assert submission.ip_address == "187.100.42.1"
        assert submission.geo_data == {"country": "BR", "city": "Sao Paulo"}
        assert submission.n8n_status == "pending"
        assert submission.server_render_time_ms > 0
        assert submission.is_duplicate is False

        # Raw UTMs preserved
        assert submission.raw_utm_data["utm_source"] == "Instagram_Reels"
        assert submission.raw_utm_data["fbclid"] == "PAZXh0bgTestFBCLID123"

    def test_create_submission_minimal_utms(self):
        """Submission with empty UTMs still creates record (no dimensions)."""
        from apps.landing.views import _create_capture_submission

        identity = IdentityFactory()
        page = CapturePageFactory(slug="wh-direct-v1")

        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.post("/inscrever-wh-direct-v1/")
        request.client_ip = None
        request.geo_data = {}
        request.device_data = None
        request.device_profile = None

        import time

        submission = _create_capture_submission(
            identity=identity,
            email_raw="direct@example.com",
            phone_raw="+5511999000111",
            capture_page=page,
            utm_data={
                "utm_source": "",
                "utm_medium": "",
                "utm_campaign": "",
                "utm_content": "",
                "utm_term": "",
                "utm_id": "",
            },
            extra_ad_params={"fbclid": "", "vk_ad_id": "", "vk_source": ""},
            capture_token=str(uuid.uuid4()),
            visitor_id="",
            request=request,
            t_start=time.monotonic(),
        )

        assert submission is not None
        # Direct traffic — dimensions should be None (direct provider has no UTMs)
        assert submission.traffic_source is None
        assert submission.ad_group is None
        assert submission.ad_creative is None
        assert submission.click_id == ""
        assert submission.n8n_status == "pending"

    def test_duplicate_detection(self):
        """Second submission with same email + launch is marked duplicate."""
        from apps.landing.views import _create_capture_submission

        identity1 = IdentityFactory()
        identity2 = IdentityFactory()
        launch = LaunchFactory(launch_code="WH0200")
        page = CapturePageFactory(slug="wh-dup-test", launch=launch)

        from django.test import RequestFactory

        rf = RequestFactory()

        import time

        def make_request():
            req = rf.post("/inscrever-wh-dup-test/")
            req.client_ip = None
            req.geo_data = {}
            req.device_data = None
            req.device_profile = None
            return req

        empty_utms = {
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "utm_id": "",
        }
        empty_extra = {"fbclid": "", "vk_ad_id": "", "vk_source": ""}

        # First submission
        sub1 = _create_capture_submission(
            identity=identity1,
            email_raw="dup@example.com",
            phone_raw="+5511999222333",
            capture_page=page,
            utm_data=empty_utms,
            extra_ad_params=empty_extra,
            capture_token=str(uuid.uuid4()),
            visitor_id="",
            request=make_request(),
            t_start=time.monotonic(),
        )
        assert sub1 is not None
        assert sub1.is_duplicate is False

        # Second submission — same email, same launch
        sub2 = _create_capture_submission(
            identity=identity2,
            email_raw="dup@example.com",
            phone_raw="+5511999444555",
            capture_page=page,
            utm_data=empty_utms,
            extra_ad_params=empty_extra,
            capture_token=str(uuid.uuid4()),
            visitor_id="",
            request=make_request(),
            t_start=time.monotonic(),
        )
        assert sub2 is not None
        assert sub2.is_duplicate is True

    def test_duplicate_case_insensitive(self):
        """Duplicate detection is case-insensitive on email."""
        from apps.landing.views import _create_capture_submission

        identity = IdentityFactory()
        launch = LaunchFactory(launch_code="WH0300")
        page = CapturePageFactory(slug="wh-case-test", launch=launch)

        from django.test import RequestFactory

        rf = RequestFactory()

        import time

        def make_request():
            req = rf.post("/test/")
            req.client_ip = None
            req.geo_data = {}
            req.device_data = None
            req.device_profile = None
            return req

        empty_utms = {
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "utm_id": "",
        }
        empty_extra = {"fbclid": "", "vk_ad_id": "", "vk_source": ""}

        # First: lowercase
        sub1 = _create_capture_submission(
            identity=identity,
            email_raw="case@test.com",
            phone_raw="+5511999111222",
            capture_page=page,
            utm_data=empty_utms,
            extra_ad_params=empty_extra,
            capture_token=str(uuid.uuid4()),
            visitor_id="",
            request=make_request(),
            t_start=time.monotonic(),
        )
        assert sub1.is_duplicate is False

        # Second: uppercase (should be detected as duplicate)
        sub2 = _create_capture_submission(
            identity=identity,
            email_raw="CASE@TEST.COM",
            phone_raw="+5511999333444",
            capture_page=page,
            utm_data=empty_utms,
            extra_ad_params=empty_extra,
            capture_token=str(uuid.uuid4()),
            visitor_id="",
            request=make_request(),
            t_start=time.monotonic(),
        )
        assert sub2.is_duplicate is True

    def test_submission_resilient_on_parser_error(self):
        """Submission creation handles UTM parser errors gracefully."""
        from unittest.mock import patch

        from apps.landing.views import _create_capture_submission

        identity = IdentityFactory()
        page = CapturePageFactory(slug="wh-err-test")

        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.post("/test/")
        request.client_ip = None
        request.geo_data = {}
        request.device_data = None
        request.device_profile = None

        import time

        # Simulate UTMParserService.parse() raising exception
        with patch(
            "apps.landing.views.UTMParserService.parse",
            side_effect=Exception("parser boom"),
        ):
            result = _create_capture_submission(
                identity=identity,
                email_raw="error@test.com",
                phone_raw="+5511999555666",
                capture_page=page,
                utm_data={"utm_source": "test"},
                extra_ad_params={},
                capture_token=str(uuid.uuid4()),
                visitor_id="",
                request=request,
                t_start=time.monotonic(),
            )

        # Should return None (not raise) — resilient
        assert result is None

    def test_factories_create_valid_submission(self):
        """Verify CaptureSubmissionFactory creates valid records."""
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        assert submission.pk is not None
        assert submission.public_id.startswith("csb_")
        assert submission.identity is not None
        assert submission.capture_page is not None
        assert submission.n8n_status == "pending"

    def test_factory_with_dimension_fks(self):
        """Factory with all dimension FKs set."""
        from tests.factories import (
            AdCreativeFactory,
            AdGroupFactory,
            CaptureSubmissionFactory,
            TrafficSourceFactory,
        )

        ts = TrafficSourceFactory()
        ag = AdGroupFactory()
        ac = AdCreativeFactory()

        submission = CaptureSubmissionFactory(
            traffic_source=ts,
            ad_group=ag,
            ad_creative=ac,
            click_id="fbclid_test_123",
            visitor_id="fp_test_xyz",
        )

        assert submission.traffic_source == ts
        assert submission.ad_group == ag
        assert submission.ad_creative == ac
        assert submission.click_id == "fbclid_test_123"


@pytest.mark.django_db
class TestN8NStatusUpdate:
    """Test n8n_status updates on CaptureSubmission."""

    def test_update_status_to_sent(self):
        """_update_submission_n8n_status sets status to 'sent'."""
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory(n8n_status="pending")

        from apps.landing.tasks import _update_submission_n8n_status

        _update_submission_n8n_status(
            submission.public_id,
            "sent",
            {"sent_at": "2026-02-17T10:00:00", "attempts": 1},
        )

        submission.refresh_from_db()
        assert submission.n8n_status == "sent"
        assert submission.n8n_response["attempts"] == 1

    def test_update_status_to_failed(self):
        """_update_submission_n8n_status sets status to 'failed'."""
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory(n8n_status="pending")

        from apps.landing.tasks import _update_submission_n8n_status

        _update_submission_n8n_status(
            submission.public_id,
            "failed",
            {"error": "max_retries_exceeded"},
        )

        submission.refresh_from_db()
        assert submission.n8n_status == "failed"

    def test_update_empty_submission_id_noop(self):
        """Empty submission_id is a no-op (no error)."""
        from apps.landing.tasks import _update_submission_n8n_status

        # Should not raise
        _update_submission_n8n_status("", "sent")

    def test_update_nonexistent_submission_noop(self):
        """Non-existent public_id is a no-op (no error)."""
        from apps.landing.tasks import _update_submission_n8n_status

        # Should not raise
        _update_submission_n8n_status("csb_nonexistent", "sent")
