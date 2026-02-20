"""
Tests for AnalyticsService — dashboard analytics aggregation.

Tests all service methods with factory-generated data.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.ads.models import CaptureSubmission
from apps.ads.services import AnalyticsService
from apps.contacts.identity.models import Identity
from apps.launches.models import CapturePage, Interest, Launch
from core.tracking.models import CaptureEvent, DeviceProfile


@pytest.fixture
def interest(db):
    return Interest.objects.create(name="Test Interest", slug="test")


@pytest.fixture
def launch(db, interest):
    return Launch.objects.create(
        name="Test Launch",
        launch_code="WH0001",
        status="active",
    )


@pytest.fixture
def capture_page(db, launch, interest):
    return CapturePage.objects.create(
        launch=launch,
        interest=interest,
        slug="test-page",
        name="Test Page",
        page_type="capture",
    )


@pytest.fixture
def device_profile(db):
    return DeviceProfile.objects.create(
        profile_hash="abcdef1234567890abcdef1234567890",
        browser_family="Chrome",
        browser_version="120.0",
        os_family="Windows",
        os_version="10",
        device_type="desktop",
    )


@pytest.fixture
def identity(db):
    return Identity.objects.create(
        status="active",
        display_name="Test User",
    )


def _make_events(capture_page, event_type: str, count: int, now):
    """Helper to create events using individual save() for public_id generation."""
    page_path = f"/inscrever-{capture_page.slug}/"
    for i in range(count):
        CaptureEvent.objects.create(
            event_type=event_type,
            capture_token=uuid4(),
            page_path=page_path,
            page_category="capture",
            capture_page=capture_page,
        )


@pytest.fixture
def capture_events(db, capture_page):
    """Create a realistic funnel of capture events."""
    now = timezone.now()
    _make_events(capture_page, "page_view", 100, now)
    _make_events(capture_page, "form_intent", 40, now)
    _make_events(capture_page, "form_attempt", 25, now)
    _make_events(capture_page, "form_success", 20, now)
    _make_events(capture_page, "form_error", 5, now)
    return CaptureEvent.objects.all()


@pytest.fixture
def submissions(db, identity, capture_page, device_profile):
    """Create capture submissions across multiple days."""
    subs = []
    for i in range(15):
        subs.append(
            CaptureSubmission.objects.create(
                identity=identity,
                email_raw=f"user{i}@test.com",
                phone_raw=f"+5511999{i:04d}",
                capture_page=capture_page,
                capture_token=uuid4(),
                device_profile=device_profile,
                ip_address="1.2.3.4",
            )
        )
    # Add 1 duplicate
    subs.append(
        CaptureSubmission.objects.create(
            identity=identity,
            email_raw="dup@test.com",
            phone_raw="+5511999999",
            capture_page=capture_page,
            capture_token=uuid4(),
            device_profile=device_profile,
            is_duplicate=True,
        )
    )
    return subs


# ===========================================================================
# Tests
# ===========================================================================


class TestGetOverviewStats:
    def test_returns_correct_keys(self, db):
        result = AnalyticsService.get_overview_stats()
        assert "total_leads" in result
        assert "total_identities" in result
        assert "conversion_rate" in result
        assert "active_launches" in result
        assert "leads_today" in result
        assert "leads_this_week" in result
        assert "wow_growth" in result

    def test_counts_non_duplicate_leads(self, submissions):
        result = AnalyticsService.get_overview_stats()
        assert result["total_leads"] == 15  # 15 non-duplicates

    def test_counts_active_identities(self, identity):
        result = AnalyticsService.get_overview_stats()
        assert result["total_identities"] == 1

    def test_counts_active_launches(self, launch):
        result = AnalyticsService.get_overview_stats()
        assert result["active_launches"] == 1

    def test_conversion_rate_calculation(self, capture_events):
        result = AnalyticsService.get_overview_stats()
        # 20 successes / 100 page_views = 20%
        assert result["conversion_rate"] == 20.0

    def test_empty_database(self, db):
        result = AnalyticsService.get_overview_stats()
        assert result["total_leads"] == 0
        assert result["conversion_rate"] == 0.0
        assert result["wow_growth"] == 0.0


class TestGetDailyTrend:
    def test_returns_correct_days(self, db):
        result = AnalyticsService.get_daily_trend(days=7)
        assert len(result) == 7

    def test_has_date_and_counts(self, db):
        result = AnalyticsService.get_daily_trend(days=7)
        for point in result:
            assert "date" in point
            assert "leads" in point
            assert "page_views" in point

    def test_counts_leads(self, submissions):
        result = AnalyticsService.get_daily_trend(days=7)
        total = sum(p["leads"] for p in result)
        # 15 non-duplicate leads across 7 days
        assert total == 15

    def test_includes_page_views(self, capture_events):
        result = AnalyticsService.get_daily_trend(days=30)
        total_views = sum(p["page_views"] for p in result)
        assert total_views == 100  # 100 page_view events


class TestGetFunnelMetrics:
    def test_returns_stages(self, capture_events):
        result = AnalyticsService.get_funnel_metrics(days=30)
        assert len(result["stages"]) == 4
        stage_names = [s["name"] for s in result["stages"]]
        assert stage_names == [
            "page_view",
            "form_intent",
            "form_attempt",
            "form_success",
        ]

    def test_stage_counts(self, capture_events):
        result = AnalyticsService.get_funnel_metrics(days=30)
        stages = {s["name"]: s["count"] for s in result["stages"]}
        assert stages["page_view"] == 100
        assert stages["form_intent"] == 40
        assert stages["form_attempt"] == 25
        assert stages["form_success"] == 20

    def test_overall_conversion(self, capture_events):
        result = AnalyticsService.get_funnel_metrics(days=30)
        assert result["overall_conversion"] == 20.0  # 20/100

    def test_error_rate(self, capture_events):
        result = AnalyticsService.get_funnel_metrics(days=30)
        assert result["form_errors"] == 5
        assert result["error_rate"] == 20.0  # 5/25 attempts

    def test_empty_funnel(self, db):
        result = AnalyticsService.get_funnel_metrics(days=30)
        assert result["overall_conversion"] == 0.0


class TestGetTopCapturePages:
    def test_returns_pages(self, submissions, capture_events):
        result = AnalyticsService.get_top_capture_pages(limit=10)
        assert len(result) == 1
        assert result[0]["slug"] == "test-page"
        assert result[0]["submissions"] == 15  # non-duplicate

    def test_includes_page_views(self, submissions, capture_events):
        result = AnalyticsService.get_top_capture_pages(limit=10)
        assert result[0]["page_views"] == 100

    def test_conversion_rate(self, submissions, capture_events):
        result = AnalyticsService.get_top_capture_pages(limit=10)
        assert result[0]["conversion_rate"] == 15.0  # 15/100

    def test_empty(self, db):
        result = AnalyticsService.get_top_capture_pages()
        assert result == []


class TestGetDeviceBreakdown:
    def test_returns_breakdown(self, submissions):
        result = AnalyticsService.get_device_breakdown(days=30)
        assert len(result) == 1
        assert result[0]["device_type"] == "desktop"
        assert result[0]["count"] == 15  # non-duplicate
        assert result[0]["percentage"] == 100.0

    def test_empty(self, db):
        result = AnalyticsService.get_device_breakdown()
        assert result == []


class TestGetUTMSourceBreakdown:
    def test_direct_traffic(self, submissions):
        result = AnalyticsService.get_utm_source_breakdown(days=30)
        # All submissions have no traffic_source = "Direct"
        assert len(result) == 1
        assert result[0]["source"] == "Direct"
        assert result[0]["count"] == 15

    def test_empty(self, db):
        result = AnalyticsService.get_utm_source_breakdown()
        assert result == []


class TestGetRecentCaptures:
    def test_returns_recent(self, submissions):
        result = AnalyticsService.get_recent_captures(limit=5)
        assert len(result) == 5

    def test_masks_email(self, submissions):
        result = AnalyticsService.get_recent_captures(limit=1)
        # Email should be masked: first char + *** + @domain
        email = result[0]["email"]
        assert "***@" in email

    def test_includes_duplicate_flag(self, submissions):
        result = AnalyticsService.get_recent_captures(limit=20)
        duplicates = [c for c in result if c["is_duplicate"]]
        assert len(duplicates) >= 1

    def test_empty(self, db):
        result = AnalyticsService.get_recent_captures()
        assert result == []


class TestGetDashboardData:
    def test_returns_all_sections(self, submissions, capture_events):
        result = AnalyticsService.get_dashboard_data()
        assert "overview" in result
        assert "daily_trend" in result
        assert "funnel" in result
        assert "top_pages" in result
        assert "device_breakdown" in result
        assert "utm_sources" in result
        assert "recent_captures" in result

    def test_empty_database(self, db):
        result = AnalyticsService.get_dashboard_data()
        assert result["overview"]["total_leads"] == 0
        assert result["funnel"]["overall_conversion"] == 0.0
        assert result["top_pages"] == []
