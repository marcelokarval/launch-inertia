"""
Tests for the launches app.

Covers:
- Interest, Launch, CapturePage model logic
- Config inheritance (Launch.default_config -> CapturePage.config)
- CapturePageService (get_page_config, get_full_config, get_page)
- Cache invalidation signals
- View integration (_resolve_campaign_config)
"""

from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.launches.models import CapturePage, Interest, Launch
from apps.launches.services import CapturePageService
from apps.launches.signals import CACHE_PREFIX, FULL_CACHE_PREFIX
from tests.factories import CapturePageFactory, InterestFactory, LaunchFactory


# ── Model Tests ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestInterestModel:
    """Tests for the Interest model."""

    def test_create_interest(self):
        interest = InterestFactory(
            name="Renda com imoveis",
            slug="rc",
            default_list_id="list_rc",
            default_thank_you_path="/obrigado-rc/",
        )
        assert interest.public_id.startswith("int_")
        assert interest.name == "Renda com imoveis"
        assert interest.slug == "rc"
        assert str(interest) == "Renda com imoveis"

    def test_interest_to_dict(self):
        interest = InterestFactory(slug="td", name="Trabalho Digital")
        d = interest.to_dict()
        assert d["slug"] == "td"
        assert d["name"] == "Trabalho Digital"
        assert "public_id" in d
        assert d["public_id"].startswith("int_")

    def test_interest_unique_slug(self):
        """Unique constraint on slug prevents duplicates at DB level."""
        from django.db import IntegrityError

        InterestFactory(slug="unique-slug")
        with pytest.raises(IntegrityError):
            Interest.objects.create(name="Duplicate", slug="unique-slug")


@pytest.mark.django_db
class TestLaunchModel:
    """Tests for the Launch model."""

    def test_create_launch(self):
        launch = LaunchFactory(
            name="Workshop Janeiro",
            launch_code="WH0126",
            status="active",
        )
        assert launch.public_id.startswith("lch_")
        assert launch.launch_code == "WH0126"
        assert str(launch) == "Workshop Janeiro (WH0126)"

    def test_launch_is_live_active(self):
        launch = LaunchFactory(
            status="active",
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        assert launch.is_live is True

    def test_launch_is_live_draft(self):
        launch = LaunchFactory(status="draft")
        assert launch.is_live is False

    def test_launch_is_live_expired(self):
        launch = LaunchFactory(
            status="active",
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(days=1),
        )
        assert launch.is_live is False

    def test_launch_is_live_not_started(self):
        launch = LaunchFactory(
            status="active",
            starts_at=timezone.now() + timedelta(days=1),
        )
        assert launch.is_live is False

    def test_launch_is_live_no_dates(self):
        launch = LaunchFactory(status="active", starts_at=None, ends_at=None)
        assert launch.is_live is True

    def test_launch_to_dict(self):
        launch = LaunchFactory(launch_code="BF2026")
        d = launch.to_dict()
        assert d["launch_code"] == "BF2026"
        assert "is_live" in d
        assert d["public_id"].startswith("lch_")

    def test_launch_unique_code(self):
        """Unique constraint on launch_code prevents duplicates at DB level."""
        from django.db import IntegrityError

        LaunchFactory(launch_code="UNIQUE01")
        with pytest.raises(IntegrityError):
            Launch.objects.create(name="Duplicate", launch_code="UNIQUE01")


@pytest.mark.django_db
class TestCapturePageModel:
    """Tests for the CapturePage model."""

    def test_create_capture_page(self):
        page = CapturePageFactory(slug="wh-rc-v3", name="Workshop RC V3")
        assert page.public_id.startswith("cpg_")
        assert page.slug == "wh-rc-v3"
        assert page.page_type == "capture"
        assert page.layout_type == "standard"

    def test_capture_page_str(self):
        launch = LaunchFactory(launch_code="WH0126")
        page = CapturePageFactory(slug="wh-rc-v3", launch=launch)
        assert str(page) == "wh-rc-v3 (WH0126)"

    def test_unique_slug(self):
        """Unique constraint on slug prevents duplicates at DB level."""
        from django.db import IntegrityError

        page = CapturePageFactory(slug="unique-page")
        with pytest.raises(IntegrityError):
            CapturePage.objects.create(
                slug="unique-page",
                name="Duplicate",
                launch=page.launch,
            )

    def test_get_resolved_config_page_overrides_launch(self):
        """Page config overrides Launch defaults (shallow merge)."""
        launch = LaunchFactory(
            default_config={
                "highlight_color": "#FF0000",
                "background_image": "/default-bg.jpg",
                "n8n": {"webhook_url": "https://default.com"},
            }
        )
        page = CapturePageFactory(
            launch=launch,
            interest=None,
            config={
                "highlight_color": "#00FF00",  # Override
                "headline": {"parts": [{"text": "Override"}]},
            },
        )
        cfg = page.get_resolved_config()
        assert cfg["highlight_color"] == "#00FF00"  # Page overrides
        assert cfg["background_image"] == "/default-bg.jpg"  # Launch default
        assert cfg["headline"]["parts"][0]["text"] == "Override"
        assert cfg["n8n"]["webhook_url"] == "https://default.com"

    def test_get_resolved_config_interest_defaults(self):
        """Interest defaults applied when not explicitly set."""
        interest = InterestFactory(
            default_list_id="list_rc",
            default_thank_you_path="/obrigado-rc/",
        )
        launch = LaunchFactory(default_config={})
        page = CapturePageFactory(
            launch=launch,
            interest=interest,
            config={},
        )
        cfg = page.get_resolved_config()
        assert cfg["n8n"]["list_id"] == "list_rc"
        assert cfg["thank_you"]["url"] == "/obrigado-rc/"

    def test_get_resolved_config_interest_does_not_override_explicit(self):
        """Explicit n8n.list_id is NOT overridden by interest defaults."""
        interest = InterestFactory(default_list_id="interest_list")
        launch = LaunchFactory(default_config={"n8n": {"list_id": "explicit_list"}})
        page = CapturePageFactory(
            launch=launch,
            interest=interest,
            config={},
        )
        cfg = page.get_resolved_config()
        assert cfg["n8n"]["list_id"] == "explicit_list"

    def test_get_resolved_config_n8n_model_fields(self):
        """n8n_webhook_url and n8n_list_id from model fields override config."""
        launch = LaunchFactory(
            default_config={"n8n": {"webhook_url": "https://from-config.com"}}
        )
        page = CapturePageFactory(
            launch=launch,
            interest=None,
            config={},
            n8n_webhook_url="https://from-model.com",
            n8n_list_id="model_list",
        )
        cfg = page.get_resolved_config()
        assert cfg["n8n"]["webhook_url"] == "https://from-model.com"
        assert cfg["n8n"]["list_id"] == "model_list"

    def test_get_resolved_config_slug_always_present(self):
        """Slug is always injected into resolved config."""
        page = CapturePageFactory(slug="my-slug", config={})
        cfg = page.get_resolved_config()
        assert cfg["slug"] == "my-slug"

    def test_to_props_shape(self):
        """to_props returns frontend-safe dict without n8n."""
        launch = LaunchFactory(
            default_config={
                "highlight_color": "#FB061A",
                "n8n": {"webhook_url": "https://secret.com"},
            }
        )
        page = CapturePageFactory(
            launch=launch,
            config={
                "meta": {"title": "Test"},
                "headline": {"parts": []},
                "form": {"button_text": "GO"},
            },
        )
        props = page.to_props()
        assert props["slug"] == page.slug
        assert props["page_type"] == "capture"
        assert props["layout_type"] == "standard"
        assert props["meta"]["title"] == "Test"
        assert props["highlight_color"] == "#FB061A"
        # n8n must NOT be in frontend props
        assert "n8n" not in props

    def test_to_dict_includes_nested(self):
        """to_dict includes launch and interest sub-dicts."""
        page = CapturePageFactory()
        d = page.to_dict()
        assert d["launch"] is not None
        assert "launch_code" in d["launch"]
        assert d["interest"] is not None
        assert "slug" in d["interest"]
        assert "config" in d

    def test_soft_delete(self):
        """Soft-deleted pages are excluded from default queryset."""
        page = CapturePageFactory(slug="soft-del")
        page.delete()  # Soft delete
        assert CapturePage.objects.filter(slug="soft-del").count() == 0
        assert CapturePage.all_objects.filter(slug="soft-del").count() == 1


# ── Service Tests ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCapturePageService:
    """Tests for CapturePageService."""

    def setup_method(self):
        cache.clear()

    def test_get_page_config_returns_props(self):
        """get_page_config returns to_props() shape."""
        page = CapturePageFactory(
            slug="svc-test",
            config={
                "meta": {"title": "Service Test"},
                "headline": {"parts": []},
            },
        )
        result = CapturePageService.get_page_config("svc-test")
        assert result is not None
        assert result["slug"] == "svc-test"
        assert result["meta"]["title"] == "Service Test"
        assert "n8n" not in result  # Frontend props only

    def test_get_page_config_none_for_missing(self):
        """get_page_config returns None for non-existent slug."""
        assert CapturePageService.get_page_config("nonexistent") is None

    def test_get_page_config_cached(self):
        """Second call hits Redis cache, not DB."""
        CapturePageFactory(slug="cached-test")
        # First call: DB hit
        result1 = CapturePageService.get_page_config("cached-test")
        # Second call: cache hit
        result2 = CapturePageService.get_page_config("cached-test")
        assert result1 == result2

    def test_get_page_config_excludes_soft_deleted(self):
        """Soft-deleted pages return None."""
        page = CapturePageFactory(slug="deleted-test")
        page.delete()  # Soft delete
        assert CapturePageService.get_page_config("deleted-test") is None

    def test_get_full_config_includes_n8n(self):
        """get_full_config returns resolved config with n8n keys."""
        launch = LaunchFactory(
            default_config={
                "n8n": {
                    "webhook_url": "https://n8n.test.com",
                    "list_id": "test_list",
                },
                "highlight_color": "#FB061A",
            }
        )
        page = CapturePageFactory(slug="full-test", launch=launch, config={})
        result = CapturePageService.get_full_config("full-test")
        assert result is not None
        assert result["n8n"]["webhook_url"] == "https://n8n.test.com"
        assert result["n8n"]["list_id"] == "test_list"
        assert result["highlight_color"] == "#FB061A"

    def test_get_full_config_injects_launch_code(self):
        """get_full_config injects launch_code into n8n section."""
        launch = LaunchFactory(launch_code="WH9999", default_config={})
        page = CapturePageFactory(slug="lc-test", launch=launch, config={})
        result = CapturePageService.get_full_config("lc-test")
        assert result is not None
        assert result["n8n"]["launch_code"] == "WH9999"

    def test_get_full_config_none_for_missing(self):
        """get_full_config returns None for non-existent slug."""
        assert CapturePageService.get_full_config("nonexistent") is None

    def test_get_full_config_cached(self):
        """get_full_config uses separate cache from get_page_config."""
        CapturePageFactory(slug="fullcache-test")
        result1 = CapturePageService.get_full_config("fullcache-test")
        result2 = CapturePageService.get_full_config("fullcache-test")
        assert result1 == result2

    def test_get_page_returns_model(self):
        """get_page returns the CapturePage model instance."""
        CapturePageFactory(slug="model-test")
        page = CapturePageService.get_page("model-test")
        assert page is not None
        assert isinstance(page, CapturePage)
        assert page.slug == "model-test"

    def test_get_page_none_for_missing(self):
        """get_page returns None for non-existent slug."""
        assert CapturePageService.get_page("nonexistent") is None


# ── Signal Tests (Cache Invalidation) ────────────────────────────────


@pytest.mark.django_db
class TestCacheInvalidationSignals:
    """Tests for cache invalidation signals."""

    def setup_method(self):
        cache.clear()

    def test_save_invalidates_props_cache(self):
        """Saving a CapturePage invalidates its props cache."""
        page = CapturePageFactory(slug="signal-save")
        # Populate cache
        CapturePageService.get_page_config("signal-save")
        assert cache.get(f"{CACHE_PREFIX}:signal-save") is not None

        # Save triggers invalidation
        page.name = "Updated Name"
        page.save()
        assert cache.get(f"{CACHE_PREFIX}:signal-save") is None

    def test_save_invalidates_full_cache(self):
        """Saving a CapturePage invalidates its full config cache."""
        page = CapturePageFactory(slug="signal-full")
        # Populate cache
        CapturePageService.get_full_config("signal-full")
        assert cache.get(f"{FULL_CACHE_PREFIX}:signal-full") is not None

        # Save triggers invalidation
        page.name = "Updated"
        page.save()
        assert cache.get(f"{FULL_CACHE_PREFIX}:signal-full") is None

    def test_delete_invalidates_cache(self):
        """Deleting a CapturePage invalidates its cache."""
        page = CapturePageFactory(slug="signal-del")
        CapturePageService.get_page_config("signal-del")
        assert cache.get(f"{CACHE_PREFIX}:signal-del") is not None

        page.hard_delete()
        assert cache.get(f"{CACHE_PREFIX}:signal-del") is None

    def test_launch_save_invalidates_all_page_caches(self):
        """Saving a Launch invalidates cache for all its pages."""
        launch = LaunchFactory()
        page1 = CapturePageFactory(slug="lch-page-1", launch=launch)
        page2 = CapturePageFactory(slug="lch-page-2", launch=launch)

        # Populate caches
        CapturePageService.get_page_config("lch-page-1")
        CapturePageService.get_page_config("lch-page-2")
        CapturePageService.get_full_config("lch-page-1")
        assert cache.get(f"{CACHE_PREFIX}:lch-page-1") is not None
        assert cache.get(f"{CACHE_PREFIX}:lch-page-2") is not None
        assert cache.get(f"{FULL_CACHE_PREFIX}:lch-page-1") is not None

        # Update launch default_config
        launch.default_config = {"highlight_color": "#00FF00"}
        launch.save()

        # All page caches invalidated
        assert cache.get(f"{CACHE_PREFIX}:lch-page-1") is None
        assert cache.get(f"{CACHE_PREFIX}:lch-page-2") is None
        assert cache.get(f"{FULL_CACHE_PREFIX}:lch-page-1") is None


# ── View Integration Tests ───────────────────────────────────────────


@pytest.mark.django_db
class TestResolveConfig:
    """Tests for _resolve_campaign_config in views."""

    def setup_method(self):
        cache.clear()

    def test_resolve_db_first(self):
        """DB config is returned when page exists in DB."""
        from apps.landing.views import _resolve_campaign_config

        CapturePageFactory(
            slug="db-first",
            config={
                "meta": {"title": "From DB"},
                "headline": {"parts": []},
            },
        )
        frontend, backend = _resolve_campaign_config("db-first")
        assert frontend is not None
        assert frontend["meta"]["title"] == "From DB"
        assert backend is not None
        # Backend should have full config including slug
        assert backend["slug"] == "db-first"

    def test_resolve_json_fallback(self):
        """JSON fallback when slug not in DB."""
        from apps.landing.views import _resolve_campaign_config

        # wh-rc-v3 exists as JSON file
        frontend, backend = _resolve_campaign_config("wh-rc-v3")
        # Should resolve (from JSON)
        assert frontend is not None
        assert backend is not None

    def test_resolve_none_for_missing(self):
        """Returns (None, None) when slug not in DB or JSON."""
        from apps.landing.views import _resolve_campaign_config

        frontend, backend = _resolve_campaign_config("totally-nonexistent-xyz")
        assert frontend is None
        assert backend is None
