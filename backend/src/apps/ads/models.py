"""
Ads & Traffic dimension models — star schema for capture analytics.

Reference tables (very low cardinality):
    AdProvider (~5-10 rows): Ad platform providers with API config.
    AdPlatform (~15-20 rows): Platforms per provider (Instagram, Facebook, etc.).

Dimension tables (low-medium cardinality, get_or_create):
    TrafficSource (~50-200 rows): Normalized platform + placement.
    AdCampaign (~50/launch): Provider campaign with Meta Campaign ID.
    AdGroup (~200/launch): Adset with payment_type + audience_temperature.
    AdCreative (~500 total): Reusable creative across launches.

Fact table:
    CaptureSubmission: One row per converted lead (replaces Baserow).

See CAPTURE_DATA_ARCHITECTURE.md for full schema rationale and field decisions.
"""

from django.db import models

from core.shared.models.base import BaseModel


# ── Reference tables (config, very low cardinality) ──────────────────


class AdProvider(models.Model):
    """Ad platform provider. Natural PK (code) — never changes.

    Stores API config and naming convention instructions for the UTM parser.
    Expected rows: ~5-10 (meta, google, tiktok, linkedin, organic, direct).
    """

    code = models.CharField(
        max_length=20,
        primary_key=True,
        help_text='Unique code: "meta", "google", "tiktok", "organic", "direct".',
    )
    name = models.CharField(
        max_length=100,
        help_text='Display name: "Meta Ads", "Google Ads", etc.',
    )

    # API integration config (varies per provider)
    api_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Provider API config: base_url, auth_type, insights_endpoint, "
            "rate_limit_per_minute, available_metrics."
        ),
    )

    # Patterns for auto-detecting this provider from UTM params
    source_patterns = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Auto-detection patterns: utm_source_patterns (regex list), "
            "vk_source_values, click_id_param."
        ),
    )

    # Instructions for UTMParserService
    naming_convention = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "UTM parsing instructions: utm_medium_separator, "
            "utm_medium_segments, utm_campaign_separator, etc."
        ),
    )

    class Meta:
        db_table = "ads_provider"
        verbose_name = "Ad Provider"
        verbose_name_plural = "Ad Providers"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class AdPlatform(models.Model):
    """Platform within a provider. E.g., Instagram under Meta.

    Expected rows: ~15-20 total across all providers.
    """

    provider = models.ForeignKey(
        AdProvider,
        on_delete=models.CASCADE,
        related_name="platforms",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text='Platform code: "instagram", "facebook", "youtube", etc.',
    )
    name = models.CharField(
        max_length=100,
        help_text='Display name: "Instagram", "Facebook", etc.',
    )

    # Platform-specific data (icon, valid placements, etc.)
    platform_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Platform metadata: icon_url, valid_placements list, default_placement."
        ),
    )

    class Meta:
        db_table = "ads_platform"
        verbose_name = "Ad Platform"
        verbose_name_plural = "Ad Platforms"
        unique_together = [("provider", "code")]
        ordering = ["provider", "code"]

    def __str__(self) -> str:
        return f"{self.name} ({self.provider.code})"


# ── Dimension tables (low-medium cardinality, get_or_create) ─────────


class TrafficSource(BaseModel):
    """Normalized platform + placement combination.

    Eliminates repeating "Instagram_Reels" across thousands of submissions.
    1000 clicks from Instagram_Reels = 1 row TrafficSource.
    Expected rows: ~50-200 total.
    """

    PUBLIC_ID_PREFIX = "tfs"

    platform = models.ForeignKey(
        AdPlatform,
        on_delete=models.CASCADE,
        related_name="traffic_sources",
        help_text="Resolves provider automatically: source.platform.provider.",
    )
    placement = models.CharField(
        max_length=50,
        help_text='Placement: "reels", "feed", "stories", "search", "shorts".',
    )

    class Meta(BaseModel.Meta):
        db_table = "ads_traffic_source"
        verbose_name = "Traffic Source"
        verbose_name_plural = "Traffic Sources"
        unique_together = [("platform", "placement")]

    def __str__(self) -> str:
        return f"{self.platform.code}_{self.placement}"


class AdCampaign(BaseModel):
    """Campaign in the ad provider. Contains Meta Campaign ID for API queries.

    Expected rows: ~50 per launch.
    """

    PUBLIC_ID_PREFIX = "acp"

    provider = models.ForeignKey(
        AdProvider,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    external_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Provider campaign ID, e.g. Meta Campaign ID. Empty for organic.",
    )
    name = models.TextField(
        help_text=(
            'Campaign name, e.g. "[WH0126] [Captacao] [Quente] [Repasse] '
            '[V1] - Melhores 2".'
        ),
    )

    # Resolved relationships (extracted from campaign name by parser)
    launch = models.ForeignKey(
        "launches.Launch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ad_campaigns",
        help_text="Auto-extracted from campaign name (WH0126 -> Launch.launch_code).",
    )
    interest = models.ForeignKey(
        "launches.Interest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ad_campaigns",
        help_text="Auto-extracted from campaign name ([Repasse] -> Interest).",
    )
    funnel_stage = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text='Funnel stage: "capture", "sales", "checkout", "content", "retention".',
    )

    # Parsed and API-enriched data (flexible schema)
    parsed_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Data derived from naming convention: temperature, "
            "page_version, variant_name, raw_campaign_string."
        ),
    )
    api_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Enriched from provider API: spend, impressions, reach, "
            "cpm, cpl, last_synced_at."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "ads_campaign"
        verbose_name = "Ad Campaign"
        verbose_name_plural = "Ad Campaigns"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                condition=models.Q(external_id__gt=""),
                name="unique_paid_campaign",
            ),
            models.UniqueConstraint(
                fields=["provider", "name", "launch"],
                condition=models.Q(external_id=""),
                name="unique_organic_campaign",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name[:60]} ({self.provider.code})"


class AdGroup(BaseModel):
    """Adset / Ad Group — operational optimization level.

    Contains the most-used dashboard filters: payment_type and
    audience_temperature, both with B-tree indexes.
    Expected rows: ~200 per launch.
    """

    PUBLIC_ID_PREFIX = "agr"

    campaign = models.ForeignKey(
        AdCampaign,
        on_delete=models.CASCADE,
        related_name="ad_groups",
        help_text="Resolves provider: ad_group.campaign.provider.",
    )
    external_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Provider adset ID, e.g. Meta Adset ID. Empty for organic.",
    )
    name = models.TextField(
        help_text='Adset name, e.g. "01 - [Mix Quente] [AD364_RC_CAPT_WH0725]".',
    )

    # Primary dashboard filters — indexed for fast WHERE clauses
    payment_type = models.CharField(
        max_length=10,
        db_index=True,
        default="paid",
        help_text='Traffic payment type: "paid" or "organic".',
    )
    audience_temperature = models.CharField(
        max_length=10,
        db_index=True,
        default="",
        blank=True,
        help_text='Audience temperature: "hot", "cold", "warm".',
    )

    # Flexible parsed and API data
    parsed_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Derived from naming convention: audience_type, "
            "sequence_number, creative_codes_in_name, raw_medium_string."
        ),
    )
    api_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Enriched from provider API: spend, impressions, reach, CPM per adset.",
    )

    class Meta(BaseModel.Meta):
        db_table = "ads_group"
        verbose_name = "Ad Group"
        verbose_name_plural = "Ad Groups"
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "external_id"],
                condition=models.Q(external_id__gt=""),
                name="unique_paid_adgroup",
            ),
            models.UniqueConstraint(
                fields=["campaign", "name"],
                condition=models.Q(external_id=""),
                name="unique_organic_adgroup",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name[:60]} ({self.campaign.provider.code})"


class AdCreative(BaseModel):
    """Advertising creative. Independent entity with own lifecycle.

    Creatives are reused across launches and cross-tested between interests.
    AD338 (Tax Deed) may run in a Repasse campaign. The creative's interest
    is independent of the campaign's interest.
    Expected rows: ~500 total (not per launch).
    """

    PUBLIC_ID_PREFIX = "acr"

    provider = models.ForeignKey(
        AdProvider,
        on_delete=models.CASCADE,
        related_name="creatives",
    )
    external_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Provider ad ID (from vk_ad_id). Empty for organic.",
    )

    # Creative identification (parsed from utm_content)
    creative_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text='Sequential creative code: "AD364" (prefix + number).',
    )
    full_code = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text='Full utm_content code: "AD364_RC_CAPT_WH0725".',
    )

    # Creative's own interest (NOT the campaign's interest)
    original_interest = models.ForeignKey(
        "launches.Interest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="creatives",
        help_text=(
            "The interest this creative was made for (RC, TD), "
            "independent of the campaign it runs in."
        ),
    )
    original_launch_code = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text=(
            'Launch where creative was originally created: "WH0725". '
            "May differ from the current launch."
        ),
    )
    funnel_stage = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text='Funnel stage from code: "capture" (CAPT), "sales", etc.',
    )

    # Provider-specific data (enriched from API)
    provider_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Provider-specific data: ad_name, format, thumbnail_url, "
            "performance metrics (ctr, cpl)."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "ads_creative"
        verbose_name = "Ad Creative"
        verbose_name_plural = "Ad Creatives"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                condition=models.Q(external_id__gt=""),
                name="unique_paid_creative",
            ),
            models.UniqueConstraint(
                fields=["provider", "full_code"],
                condition=models.Q(external_id="") & models.Q(full_code__gt=""),
                name="unique_organic_creative",
            ),
        ]

    def __str__(self) -> str:
        label = self.full_code or self.creative_code or self.external_id
        return f"{label} ({self.provider.code})"


# ── Fact table: CaptureSubmission ────────────────────────────────────


class CaptureSubmission(BaseModel):
    """One row per converted lead. Direct replacement for Baserow.

    All dimensions are FKs — zero data repetition.
    The capture_token is a logical join (not FK) to CaptureEvent records.

    See CAPTURE_DATA_ARCHITECTURE.md section 5.4 for full field rationale.
    """

    PUBLIC_ID_PREFIX = "csb"

    # -- Pyright: FK auto-generated _id attributes --
    capture_page_id: int
    identity_id: int

    # ── WHO ──
    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.CASCADE,
        related_name="capture_submissions",
        help_text="Resolved by ResolutionService. Always set (PHASE 3 guarantees).",
    )
    email_raw = models.CharField(
        max_length=254,
        help_text="Exact form value (before normalization).",
    )
    phone_raw = models.CharField(
        max_length=30,
        help_text="Exact form value.",
    )

    # ── WHERE ──
    capture_page = models.ForeignKey(
        "launches.CapturePage",
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="Resolves everything: launch, interest, slug, n8n config.",
    )

    # ── TRAFFIC (normalized dimensions) ──
    traffic_source = models.ForeignKey(
        TrafficSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        help_text="Null if direct traffic (no utm_source).",
    )
    ad_group = models.ForeignKey(
        AdGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        help_text="Null if organic without adset. Resolves -> campaign -> provider.",
    )
    ad_creative = models.ForeignKey(
        AdCreative,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        help_text="Null if no parseable utm_content.",
    )

    click_id = models.CharField(
        max_length=200,
        blank=True,
        default="",
        db_index=True,
        help_text="fbclid / gclid / ttclid — unique per click. Essential for Meta CAPI.",
    )

    # ── FINGERPRINT ──
    visitor_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text="FingerprintJS visitorId.",
    )

    # ── TRACKING ──
    capture_token = models.UUIDField(
        db_index=True,
        help_text="Logical join with CaptureEvents (not FK). UUID from GET.",
    )
    device_profile = models.ForeignKey(
        "tracking.DeviceProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        help_text="Device dimension from VisitorMiddleware.",
    )

    # ── NETWORK ──
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )
    geo_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="GeoIP: {city, region, country, lat, lng, asn, isp}.",
    )

    # ── N8N ──
    n8n_status = models.CharField(
        max_length=20,
        default="pending",
        db_index=True,
        help_text='Status: "pending", "sent", "failed", "skipped".',
    )
    n8n_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Webhook response for debug/retry: status_code, sent_at, attempts.",
    )

    # ── METRICS ──
    server_render_time_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="View render time (time.monotonic). Performance monitoring.",
    )
    is_duplicate = models.BooleanField(
        default=False,
        help_text="Same email + same launch already existed.",
    )

    # ── RAW UTM (preserved for re-parsing / audit) ──
    raw_utm_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Original UTM parameters as received from frontend. "
            "Preserved for re-parsing when naming conventions change."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "ads_capture_submission"
        verbose_name = "Capture Submission"
        verbose_name_plural = "Capture Submissions"
        indexes = [
            models.Index(fields=["capture_page", "created_at"]),
            models.Index(fields=["capture_token"]),
            models.Index(fields=["n8n_status"]),
            models.Index(fields=["visitor_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Submission({self.email_raw}, {self.capture_page_id})"
