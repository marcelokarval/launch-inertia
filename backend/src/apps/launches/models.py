"""
Launch management models.

Provides the config-driven page system that replaces static JSON campaign files.
A Launch owns multiple CapturePages, each optionally linked to an Interest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

from core.shared.models.base import BaseModel

if TYPE_CHECKING:
    from django.db.models import Manager


class Interest(BaseModel):
    """Segmentation category for capture pages.

    Examples: rc (renda com) , td (trabalho digital), ds (do zero ao sucesso),
    cp (como publicar), bf (black friday).
    Each interest defines defaults that its pages inherit.
    """

    PUBLIC_ID_PREFIX = "int"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    # CRM integration defaults (inherited by pages unless overridden)
    default_list_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Default CRM list ID for leads captured via this interest.",
    )
    default_thank_you_path = models.CharField(
        max_length=200,
        blank=True,
        help_text="Default thank-you path, e.g. /obrigado-wh-rc-v3/",
    )

    class Meta(BaseModel.Meta):
        db_table = "launches_interest"
        verbose_name = "Interest"
        verbose_name_plural = "Interests"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        return {
            "public_id": self.public_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "default_list_id": self.default_list_id,
            "default_thank_you_path": self.default_thank_you_path,
        }


class Launch(BaseModel):
    """A digital product launch campaign.

    A launch groups multiple capture pages under a single campaign with
    shared defaults (launch_code, dates, endpoints, branding).
    """

    PUBLIC_ID_PREFIX = "lch"

    # -- Pyright: reverse relation managers --
    if TYPE_CHECKING:
        pages: Manager[CapturePage]

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=200)
    launch_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique code, e.g. WH0126, BF2026.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    description = models.TextField(blank=True)

    # Dates
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    # Default config inherited by all pages unless overridden
    default_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Shared defaults for all pages: highlight_color, "
            "n8n webhook_url, form gradients, trust_badge, social_proof, etc."
        ),
    )

    class Meta(BaseModel.Meta):
        db_table = "launches_launch"
        verbose_name = "Launch"
        verbose_name_plural = "Launches"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.launch_code})"

    @property
    def is_live(self) -> bool:
        """Check if launch is currently active and within dates."""
        if self.status != self.Status.ACTIVE:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "public_id": self.public_id,
            "name": self.name,
            "launch_code": self.launch_code,
            "status": self.status,
            "is_live": self.is_live,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
        }


class CapturePage(BaseModel):
    """A config-driven landing page belonging to a Launch.

    Replaces static JSON campaign files. Each page stores its full visual
    and behavioral config in a JSONField, inheriting defaults from its
    Launch and optionally from its Interest.
    """

    PUBLIC_ID_PREFIX = "cpg"

    # -- Pyright: FK auto-generated _id attributes --
    launch_id: int
    interest_id: int | None

    class PageType(models.TextChoices):
        CAPTURE = "capture", "Captura (email + phone)"
        WAITLIST = "waitlist", "Lista de espera (email only)"
        CPL = "cpl", "CPL (conteudo + captura)"
        CHECKOUT = "checkout", "Checkout (redirect para Stripe)"
        CONTENT = "content", "Conteudo (blog, artigo)"
        SALES = "sales", "Pagina de vendas"

    class LayoutType(models.TextChoices):
        STANDARD = "standard", "Standard (single column)"
        TWO_COLUMN = "two-column", "Two Column (Black Friday style)"

    # Relationships
    launch = models.ForeignKey(
        Launch,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    interest = models.ForeignKey(
        Interest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
    )

    # Identification
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL slug, e.g. wh-rc-v3. Route: /inscrever-{slug}/",
    )
    name = models.CharField(
        max_length=200,
        help_text="Internal name for admin identification.",
    )

    # Type and layout
    page_type = models.CharField(
        max_length=20,
        choices=PageType.choices,
        default=PageType.CAPTURE,
    )
    layout_type = models.CharField(
        max_length=20,
        choices=LayoutType.choices,
        default=LayoutType.STANDARD,
    )

    # Full page config — overrides Launch.default_config per-page
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Page-specific config. Keys: meta, headline, subheadline, "
            "background_image, highlight_color, badges, form, trust_badge, "
            "social_proof, thank_you, n8n, topBanner, etc. "
            "Missing keys fall back to Launch.default_config."
        ),
    )

    # N8N integration
    n8n_webhook_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="N8N webhook URL for this page. Overrides launch default.",
    )
    n8n_list_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="CRM list ID for leads from this page.",
    )

    class Meta(BaseModel.Meta):
        db_table = "launches_capture_page"
        verbose_name = "Capture Page"
        verbose_name_plural = "Capture Pages"
        ordering = ["slug"]

    def __str__(self) -> str:
        return f"{self.slug} ({self.launch.launch_code})"

    def get_resolved_config(self) -> dict:
        """Resolve full config with inheritance: Launch defaults → Page overrides.

        Returns a merged dict where page-level config overrides launch defaults.
        """
        base = dict(self.launch.default_config) if self.launch.default_config else {}
        page = dict(self.config) if self.config else {}

        # Shallow merge: page values override launch defaults
        resolved = {**base, **page}

        # Ensure slug is always present
        resolved["slug"] = self.slug

        # Apply interest defaults if not explicitly set
        if self.interest:
            if "n8n" not in resolved:
                resolved["n8n"] = {}
            n8n = resolved["n8n"]
            if not n8n.get("list_id") and self.interest.default_list_id:
                n8n["list_id"] = self.interest.default_list_id
            if not resolved.get("thank_you", {}).get("url"):
                if self.interest.default_thank_you_path:
                    resolved.setdefault("thank_you", {})["url"] = (
                        self.interest.default_thank_you_path
                    )

        # Apply n8n fields from model if set
        if self.n8n_webhook_url:
            resolved.setdefault("n8n", {})["webhook_url"] = self.n8n_webhook_url
        if self.n8n_list_id:
            resolved.setdefault("n8n", {})["list_id"] = self.n8n_list_id

        return resolved

    def to_dict(self) -> dict:
        return {
            "public_id": self.public_id,
            "slug": self.slug,
            "name": self.name,
            "page_type": self.page_type,
            "layout_type": self.layout_type,
            "launch": self.launch.to_dict() if self.launch_id else None,
            "interest": self.interest.to_dict() if self.interest_id else None,
            "config": self.get_resolved_config(),
        }

    def to_props(self) -> dict:
        """Build the props dict to send to the Inertia frontend.

        This is the primary method views should call. It returns a flat
        dict matching the shape the frontend Capture/Index component expects.
        """
        cfg = self.get_resolved_config()

        props: dict = {
            "slug": self.slug,
            "page_type": self.page_type,
            "layout_type": self.layout_type,
        }

        # Pass through known config keys
        for key in (
            "meta",
            "headline",
            "subheadline",
            "badges",
            "form",
            "trust_badge",
            "social_proof",
            "thank_you",
            "background_image",
            "highlight_color",
            "topBanner",
        ):
            if key in cfg:
                props[key] = cfg[key]

        return props
