"""
Tracking models — universal event tracking and device profiling.

DeviceProfile: Dimension table (star schema, hash-based dedup).
    ~200-1000 rows. Each unique browser+OS+device = 1 row.
    CaptureEvent stores a 4-byte FK instead of ~200 bytes of strings.

CaptureEvent: Universal tracker for ALL pages (not just capture).
    Tracks page_view, form_attempt, form_success, form_error, cta_click.
    capture_token links events within the same page load session.

TrackingDailySummary: Materialized view — read-only, refreshed by Celery.
TrackingPageMetrics: Non-materialized view — always fresh, slower.
"""

import hashlib

from django.db import models

from core.shared.models.base import BaseModel


# ── DeviceProfile (dimension table) ──────────────────────────────────


class DeviceProfile(BaseModel):
    """Normalized device profile. Created ONCE, referenced by many events.

    Pattern: star schema (Matomo). Hash-based dedup via profile_hash.
    Expected cardinality: ~200-1,000 rows (vs millions of events).
    Each event stores only a 4-byte FK instead of ~200 bytes of strings.
    """

    PUBLIC_ID_PREFIX = "dpf"

    # Hash for fast dedup (SHA-256 truncated, 32 hex chars)
    # Computed from: browser_family|browser_version_major|os_family|os_version|device_type
    profile_hash = models.CharField(max_length=32, unique=True, db_index=True)

    # ─── BROWSER ───
    browser_family = models.CharField(max_length=50)
    browser_version = models.CharField(max_length=20)
    browser_engine = models.CharField(max_length=30, blank=True)

    # ─── OS ───
    os_family = models.CharField(max_length=50)
    os_version = models.CharField(max_length=20, blank=True)

    # ─── DEVICE ───
    device_type = models.CharField(max_length=20)
    device_brand = models.CharField(max_length=50, blank=True)
    device_model = models.CharField(max_length=50, blank=True)

    # ─── BOT ───
    is_bot = models.BooleanField(default=False)
    bot_name = models.CharField(max_length=100, blank=True)
    bot_category = models.CharField(max_length=50, blank=True)

    # ─── DEBUG ───
    user_agent_sample = models.TextField(
        blank=True,
        help_text="One example UA string for debugging.",
    )

    class Meta(BaseModel.Meta):
        db_table = "tracking_device_profile"
        indexes = [
            models.Index(fields=["browser_family", "os_family"]),
            models.Index(fields=["device_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.browser_family} {self.browser_version} / {self.os_family} / {self.device_type}"

    @classmethod
    def compute_hash(
        cls,
        browser_family: str,
        browser_version: str,
        os_family: str,
        os_version: str,
        device_type: str,
    ) -> str:
        """Deterministic hash from normalized attributes.

        Only the major browser version is used (e.g., "120.0.6099" -> "120").
        """
        major_version = browser_version.split(".")[0] if browser_version else ""
        parts = [
            browser_family.lower().strip(),
            major_version,
            os_family.lower().strip(),
            os_version.lower().strip(),
            device_type.lower().strip(),
        ]
        canonical = "|".join(parts)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


# ── CaptureEvent (universal tracker) ────────────────────────────────


class CaptureEvent(BaseModel):
    """Universal event tracker for ALL pages in the system.

    NOT coupled to capture pages only. Tracks:
    - Landing pages (capture, checkout, thank-you, support, sales, content)
    - Dashboard (future)
    - Any page where tracking is needed

    The capture_token groups all events from the same page load session
    (GET page_view -> POST form_attempt -> form_success/form_error).
    """

    PUBLIC_ID_PREFIX = "cev"

    class EventType(models.TextChoices):
        PAGE_VIEW = "page_view", "Page View"
        FORM_ATTEMPT = "form_attempt", "Form Attempt"
        FORM_SUCCESS = "form_success", "Form Success"
        FORM_ERROR = "form_error", "Form Error"
        CTA_CLICK = "cta_click", "CTA Click"
        SCROLL_MILESTONE = "scroll_milestone", "Scroll Milestone"

    class PageCategory(models.TextChoices):
        CAPTURE = "capture", "Pagina de Captura"
        CHECKOUT = "checkout", "Checkout"
        THANK_YOU = "thank_you", "Obrigado"
        SUPPORT = "support", "Suporte"
        SALES = "sales", "Pagina de Vendas"
        CONTENT = "content", "Conteudo"
        LEGAL = "legal", "Pagina Legal"
        DASHBOARD = "dashboard", "Dashboard"
        OTHER = "other", "Outro"

    # ─── EVENT ───
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        db_index=True,
    )

    # Token per page load — groups events from the same visit
    capture_token = models.UUIDField(
        db_index=True,
        help_text=(
            "UUID generated on GET, passed as prop + hidden input. "
            "Links page_view -> form_attempt -> form_success of the same session."
        ),
    )

    # ─── PAGE (universal, not coupled to capture) ───
    page_path = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Path: /inscrever-wh-rc-v3/, /obrigado-wh-rc-v3/, /suporte/, etc.",
    )
    page_category = models.CharField(
        max_length=20,
        choices=PageCategory.choices,
        default=PageCategory.OTHER,
        db_index=True,
    )
    page_url = models.URLField(max_length=500, blank=True)
    referrer = models.URLField(max_length=500, blank=True)

    # ─── IDENTITY (all optional — allows anonymous events) ───
    fingerprint_identity = models.ForeignKey(
        "contact_fingerprint.FingerprintIdentity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracking_events",
    )
    identity = models.ForeignKey(
        "contact_identity.Identity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracking_events",
    )

    # ─── DEVICE (FK to dimension table — 4 bytes, not repeated strings) ───
    device_profile = models.ForeignKey(
        DeviceProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # ─── REFERENCE TO CAPTURE PAGE (optional, only for page_category=capture) ───
    capture_page = models.ForeignKey(
        "launches.CapturePage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # ─── NETWORK ───
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    geo_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="GeoIP data: {city, country, lat, long, asn, isp}",
    )

    # ─── VISITOR ───
    visitor_id = models.CharField(max_length=100, blank=True, db_index=True)

    # ─── CONTEXT ───
    utm_data = models.JSONField(default=dict, blank=True)
    accept_language = models.CharField(max_length=100, blank=True)

    # ─── EXTENSIBLE ───
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Extra data: validation errors, scroll_depth, time_on_page, cta_label, etc."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "tracking_capture_event"
        ordering = ["-created_at"]
        indexes = [
            # Funnel queries by page
            models.Index(fields=["page_path", "event_type", "created_at"]),
            # Queries by page category
            models.Index(fields=["page_category", "event_type", "created_at"]),
            # Group events of the same session
            models.Index(fields=["capture_token", "event_type"]),
            # Visitor history
            models.Index(fields=["visitor_id", "created_at"]),
            # Partial index: page_views only (majority of queries)
            models.Index(
                fields=["created_at"],
                name="idx_cev_pageview_ts",
                condition=models.Q(event_type="page_view"),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.page_path} ({self.capture_token})"


# ── Unmanaged models for SQL views ──────────────────────────────────


class TrackingDailySummary(models.Model):
    """Materialized view — read-only, refreshed by Celery beat.

    Aggregates events by page_path, page_category, date, event_type.
    Provides fast pre-computed analytics.
    """

    page_path = models.CharField(max_length=500)
    page_category = models.CharField(max_length=20)
    date = models.DateField()
    event_type = models.CharField(max_length=20)
    event_count = models.IntegerField()
    unique_visitors = models.IntegerField()
    unique_ips = models.IntegerField()

    class Meta:
        managed = False
        db_table = "tracking_daily_summary"


class TrackingPageMetrics(models.Model):
    """Non-materialized view — always fresh, may be slower for large datasets.

    Provides per-page conversion metrics (views, attempts, conversions, errors).
    """

    page_path = models.CharField(max_length=500, primary_key=True)
    page_category = models.CharField(max_length=20)
    views = models.IntegerField()
    attempts = models.IntegerField()
    conversions = models.IntegerField()
    errors = models.IntegerField()
    conversion_rate_pct = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = "tracking_page_metrics"
