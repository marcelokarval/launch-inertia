"""
AnalyticsService — dashboard analytics aggregation.

Provides pre-computed stats for the dashboard from all tracking/capture models:
- Overview stats (total leads, identities, conversion rate, active launches)
- Daily capture trend (last N days)
- Funnel metrics (page_view → form_intent → form_attempt → form_success)
- Top capture pages by conversions
- Device breakdown (desktop/mobile/tablet)
- UTM source breakdown
- Recent captures list
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone


class AnalyticsService:
    """Stateless service with classmethods for dashboard analytics."""

    @classmethod
    def get_overview_stats(cls) -> dict[str, Any]:
        """Top-level stats for the 4 dashboard stat cards.

        Returns:
            total_leads: Total CaptureSubmission count (non-deleted, non-duplicate)
            total_identities: Active Identity count
            conversion_rate: Overall form_success / page_view ratio (capture pages)
            active_launches: Launches with status='active'
            leads_today: Leads captured today
            leads_this_week: Leads captured in last 7 days
        """
        from apps.ads.models import CaptureSubmission
        from apps.contacts.identity.models import Identity
        from apps.launches.models import Launch
        from core.tracking.models import CaptureEvent

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        # Lead counts
        base_leads = CaptureSubmission.objects.filter(
            is_deleted=False, is_duplicate=False
        )
        total_leads = base_leads.count()
        leads_today = base_leads.filter(created_at__gte=today_start).count()
        leads_this_week = base_leads.filter(created_at__gte=week_start).count()

        # Previous week for comparison
        prev_week_start = week_start - timedelta(days=7)
        leads_prev_week = base_leads.filter(
            created_at__gte=prev_week_start,
            created_at__lt=week_start,
        ).count()

        # Week-over-week growth
        if leads_prev_week > 0:
            wow_growth = round(
                ((leads_this_week - leads_prev_week) / leads_prev_week) * 100, 1
            )
        else:
            wow_growth = 100.0 if leads_this_week > 0 else 0.0

        # Identities
        total_identities = Identity.objects.filter(
            is_deleted=False, status="active"
        ).count()

        # Conversion rate: form_success / page_view for capture pages
        capture_events = CaptureEvent.objects.filter(
            page_category="capture",
        )
        page_views = capture_events.filter(event_type="page_view").count()
        form_successes = capture_events.filter(event_type="form_success").count()
        conversion_rate = (
            round((form_successes / page_views) * 100, 1) if page_views > 0 else 0.0
        )

        # Active launches
        active_launches = Launch.objects.filter(status="active").count()

        return {
            "total_leads": total_leads,
            "leads_today": leads_today,
            "leads_this_week": leads_this_week,
            "leads_prev_week": leads_prev_week,
            "wow_growth": wow_growth,
            "total_identities": total_identities,
            "conversion_rate": conversion_rate,
            "active_launches": active_launches,
            "total_page_views": page_views,
            "total_form_successes": form_successes,
        }

    @classmethod
    def get_daily_trend(cls, days: int = 30) -> list[dict[str, Any]]:
        """Daily lead capture count for the last N days.

        Returns list of {date: "YYYY-MM-DD", leads: int, page_views: int}.
        """
        from apps.ads.models import CaptureSubmission
        from core.tracking.models import CaptureEvent

        since = timezone.now() - timedelta(days=days)

        # Leads per day
        leads_by_day = dict(
            CaptureSubmission.objects.filter(
                is_deleted=False, is_duplicate=False, created_at__gte=since
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .values_list("date", "count")
        )

        # Page views per day (capture pages only)
        views_by_day = dict(
            CaptureEvent.objects.filter(
                event_type="page_view",
                page_category="capture",
                created_at__gte=since,
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .values_list("date", "count")
        )

        # Build complete date range
        result: list[dict[str, Any]] = []
        today = timezone.now().date()
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            result.append(
                {
                    "date": d.isoformat(),
                    "leads": leads_by_day.get(d, 0),
                    "page_views": views_by_day.get(d, 0),
                }
            )
        return result

    @classmethod
    def get_funnel_metrics(cls, days: int = 30) -> dict[str, Any]:
        """Capture funnel: page_view → form_intent → form_attempt → form_success.

        Returns counts and stage-to-stage conversion rates.
        """
        from core.tracking.models import CaptureEvent

        since = timezone.now() - timedelta(days=days)
        events = CaptureEvent.objects.filter(
            page_category="capture",
            created_at__gte=since,
        )

        counts = dict(
            events.values("event_type")
            .annotate(count=Count("id"))
            .values_list("event_type", "count")
        )

        page_views = counts.get("page_view", 0)
        form_intents = counts.get("form_intent", 0)
        form_attempts = counts.get("form_attempt", 0)
        form_successes = counts.get("form_success", 0)
        form_errors = counts.get("form_error", 0)

        def pct(a: int, b: int) -> float:
            return round((a / b) * 100, 1) if b > 0 else 0.0

        return {
            "stages": [
                {
                    "name": "page_view",
                    "label": "Visualizacoes",
                    "count": page_views,
                    "rate": 100.0,
                },
                {
                    "name": "form_intent",
                    "label": "Intencao",
                    "count": form_intents,
                    "rate": pct(form_intents, page_views),
                },
                {
                    "name": "form_attempt",
                    "label": "Tentativas",
                    "count": form_attempts,
                    "rate": pct(form_attempts, page_views),
                },
                {
                    "name": "form_success",
                    "label": "Conversoes",
                    "count": form_successes,
                    "rate": pct(form_successes, page_views),
                },
            ],
            "form_errors": form_errors,
            "error_rate": pct(form_errors, form_attempts),
            "overall_conversion": pct(form_successes, page_views),
        }

    @classmethod
    def get_top_capture_pages(cls, limit: int = 10) -> list[dict[str, Any]]:
        """Top capture pages by submission count.

        Returns list of {slug, name, launch_name, submissions, page_views,
        conversion_rate}.
        """
        from apps.ads.models import CaptureSubmission
        from apps.launches.models import CapturePage
        from core.tracking.models import CaptureEvent

        # Top pages by submissions
        top_pages = (
            CaptureSubmission.objects.filter(is_deleted=False, is_duplicate=False)
            .values("capture_page_id")
            .annotate(submissions=Count("id"))
            .order_by("-submissions")[:limit]
        )

        page_ids = [p["capture_page_id"] for p in top_pages]
        submission_map = {p["capture_page_id"]: p["submissions"] for p in top_pages}

        # Page views for these capture pages
        pages = CapturePage.objects.filter(id__in=page_ids).select_related("launch")

        # Count page_views per capture page
        page_view_counts = dict(
            CaptureEvent.objects.filter(
                capture_page_id__in=page_ids,
                event_type="page_view",
            )
            .values("capture_page_id")
            .annotate(count=Count("id"))
            .values_list("capture_page_id", "count")
        )

        result: list[dict[str, Any]] = []
        for page in pages:
            submissions = submission_map.get(page.id, 0)
            views = page_view_counts.get(page.id, 0)
            rate = round((submissions / views) * 100, 1) if views > 0 else 0.0
            result.append(
                {
                    "slug": page.slug,
                    "name": page.name,
                    "launch_name": page.launch.name if page.launch else "",
                    "submissions": submissions,
                    "page_views": views,
                    "conversion_rate": rate,
                }
            )

        result.sort(key=lambda x: x["submissions"], reverse=True)
        return result

    @classmethod
    def get_device_breakdown(cls, days: int = 30) -> list[dict[str, Any]]:
        """Device type distribution from CaptureSubmission → DeviceProfile.

        Returns list of {device_type, count, percentage}.
        """
        from apps.ads.models import CaptureSubmission

        since = timezone.now() - timedelta(days=days)

        breakdown = (
            CaptureSubmission.objects.filter(
                is_deleted=False,
                is_duplicate=False,
                created_at__gte=since,
                device_profile__isnull=False,
            )
            .values(device_type=F("device_profile__device_type"))
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        total = sum(item["count"] for item in breakdown)
        result: list[dict[str, Any]] = []
        for item in breakdown:
            result.append(
                {
                    "device_type": item["device_type"] or "unknown",
                    "count": item["count"],
                    "percentage": (
                        round((item["count"] / total) * 100, 1) if total > 0 else 0.0
                    ),
                }
            )
        return result

    @classmethod
    def get_utm_source_breakdown(cls, days: int = 30) -> list[dict[str, Any]]:
        """UTM source distribution from CaptureSubmission → TrafficSource → Platform → Provider.

        Returns list of {source, platform, count, percentage}.
        """
        from apps.ads.models import CaptureSubmission

        since = timezone.now() - timedelta(days=days)

        breakdown = (
            CaptureSubmission.objects.filter(
                is_deleted=False,
                is_duplicate=False,
                created_at__gte=since,
                traffic_source__isnull=False,
            )
            .values(
                source=F("traffic_source__platform__provider__name"),
                platform=F("traffic_source__platform__name"),
            )
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Include direct traffic (no traffic_source)
        direct_count = CaptureSubmission.objects.filter(
            is_deleted=False,
            is_duplicate=False,
            created_at__gte=since,
            traffic_source__isnull=True,
        ).count()

        result: list[dict[str, Any]] = list(breakdown)
        if direct_count > 0:
            result.append(
                {
                    "source": "Direct",
                    "platform": "Direct",
                    "count": direct_count,
                }
            )

        total = sum(item["count"] for item in result)
        for item in result:
            item["percentage"] = (
                round((item["count"] / total) * 100, 1) if total > 0 else 0.0
            )

        result.sort(key=lambda x: x["count"], reverse=True)
        return result

    @classmethod
    def get_recent_captures(cls, limit: int = 15) -> list[dict[str, Any]]:
        """Most recent capture submissions for the activity feed.

        Returns list of {id, email, phone, page_slug, page_name, source,
        device_type, created_at, is_duplicate}.
        """
        from apps.ads.models import CaptureSubmission

        captures = (
            CaptureSubmission.objects.filter(is_deleted=False)
            .select_related(
                "capture_page",
                "device_profile",
                "traffic_source__platform__provider",
            )
            .order_by("-created_at")[:limit]
        )

        result: list[dict[str, Any]] = []
        for c in captures:
            # Mask email for privacy: j***@gmail.com
            email_parts = c.email_raw.split("@")
            masked_email = (
                f"{email_parts[0][0]}***@{email_parts[1]}"
                if len(email_parts) == 2 and email_parts[0]
                else c.email_raw
            )

            source_name = ""
            if c.traffic_source and c.traffic_source.platform:
                source_name = c.traffic_source.platform.provider.name

            result.append(
                {
                    "id": c.public_id,
                    "email": masked_email,
                    "phone": c.phone_raw[-4:] if c.phone_raw else "",
                    "page_slug": c.capture_page.slug if c.capture_page else "",
                    "page_name": c.capture_page.name if c.capture_page else "",
                    "source": source_name or "Direct",
                    "device_type": (
                        c.device_profile.device_type if c.device_profile else "unknown"
                    ),
                    "created_at": c.created_at.isoformat() if c.created_at else "",
                    "is_duplicate": c.is_duplicate,
                }
            )
        return result

    @classmethod
    def get_dashboard_data(cls) -> dict[str, Any]:
        """Full dashboard payload — all analytics in one call.

        Called by the dashboard view to build the complete props object.
        """
        return {
            "overview": cls.get_overview_stats(),
            "daily_trend": cls.get_daily_trend(days=30),
            "funnel": cls.get_funnel_metrics(days=30),
            "top_pages": cls.get_top_capture_pages(limit=10),
            "device_breakdown": cls.get_device_breakdown(days=30),
            "utm_sources": cls.get_utm_source_breakdown(days=30),
            "recent_captures": cls.get_recent_captures(limit=15),
        }
