"""
Dedicated tests for LifecycleService + expand-on-demand endpoint.

Tests cover:
- Empty schema generation
- Full recalculation (channels, timeline, scores, tags, behavior)
- Partial section updates (launches, financial, behavior)
- record_entry helper
- Schema forward-compatibility (_ensure_schema_fields)
- LTV tier calculation
- Expand-on-demand data loading
- Expand endpoint (JSON API)
- Recalculate endpoint (JSON API)
"""

import json
from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.contacts.identity.models import Identity
from apps.contacts.identity.services.lifecycle_service import (
    LifecycleService,
    LIFECYCLE_SCHEMA_VERSION,
)
from tests.factories import (
    IdentityFactory,
    ContactEmailFactory,
    ContactPhoneFactory,
    TagFactory,
    UserFactory,
)


# ── Schema Tests ──────────────────────────────────────────────────────


class TestEmptySchema:
    """Tests for get_empty_schema()."""

    def test_has_correct_version(self):
        schema = LifecycleService.get_empty_schema()
        assert schema["_version"] == LIFECYCLE_SCHEMA_VERSION

    def test_has_all_sections(self):
        schema = LifecycleService.get_empty_schema()
        expected_sections = {
            "_version",
            "_updated_at",
            "timeline",
            "launches",
            "financial",
            "behavior",
            "channels",
            "tags",
            "scores",
        }
        assert set(schema.keys()) == expected_sections

    def test_timeline_section_defaults(self):
        schema = LifecycleService.get_empty_schema()
        timeline = schema["timeline"]
        assert timeline["first_seen"] is None
        assert timeline["last_seen"] is None
        assert timeline["first_purchase"] is None
        assert timeline["days_since_first_seen"] is None

    def test_launches_section_defaults(self):
        schema = LifecycleService.get_empty_schema()
        launches = schema["launches"]
        assert launches["total_participated"] == 0
        assert launches["active"] == []
        assert launches["history"] == []
        assert launches["is_recurrent"] is False

    def test_financial_section_defaults(self):
        schema = LifecycleService.get_empty_schema()
        financial = schema["financial"]
        assert financial["total_spent"] == 0.0
        assert financial["currency"] == "BRL"
        assert financial["products_purchased"] == []
        assert financial["is_delinquent"] is False

    def test_channels_section_defaults(self):
        schema = LifecycleService.get_empty_schema()
        channels = schema["channels"]
        assert channels["emails"]["total"] == 0
        assert channels["phones"]["whatsapp"] == 0
        assert channels["fingerprints"]["devices"] == []

    def test_scores_section_defaults(self):
        schema = LifecycleService.get_empty_schema()
        scores = schema["scores"]
        assert scores["confidence"] == 0.0
        assert scores["ltv_tier"] is None


# ── Recalculation Tests ──────────────────────────────────────────────


@pytest.mark.django_db
class TestRecalculate:
    """Tests for full recalculation."""

    def test_recalculate_empty_identity(self):
        """Recalculation on identity with no channels produces correct schema."""
        identity = IdentityFactory()
        lifecycle = LifecycleService.recalculate(identity)

        assert lifecycle["_version"] == LIFECYCLE_SCHEMA_VERSION
        assert lifecycle["_updated_at"] is not None
        assert lifecycle["channels"]["emails"]["total"] == 0
        assert lifecycle["channels"]["phones"]["total"] == 0
        assert lifecycle["channels"]["fingerprints"]["total"] == 0

    def test_recalculate_with_emails(self):
        """Recalculation picks up email channels."""
        identity = IdentityFactory()
        ContactEmailFactory(identity=identity, value="first@test.com", is_verified=True)
        ContactEmailFactory(
            identity=identity, value="second@test.com", is_verified=False
        )

        lifecycle = LifecycleService.recalculate(identity)

        assert lifecycle["channels"]["emails"]["total"] == 2
        assert lifecycle["channels"]["emails"]["verified"] == 1
        assert lifecycle["channels"]["emails"]["primary"] == "first@test.com"

    def test_recalculate_with_phones(self):
        """Recalculation picks up phone channels."""
        identity = IdentityFactory()
        ContactPhoneFactory(
            identity=identity,
            value="+5511999000001",
            is_verified=True,
            is_whatsapp=True,
        )
        ContactPhoneFactory(
            identity=identity,
            value="+5511999000002",
            is_verified=False,
            is_whatsapp=False,
        )

        lifecycle = LifecycleService.recalculate(identity)

        assert lifecycle["channels"]["phones"]["total"] == 2
        assert lifecycle["channels"]["phones"]["verified"] == 1
        assert lifecycle["channels"]["phones"]["whatsapp"] == 1

    def test_recalculate_timeline(self):
        """Timeline section is populated from Identity timestamps."""
        identity = IdentityFactory()
        lifecycle = LifecycleService.recalculate(identity)

        assert lifecycle["timeline"]["first_seen"] is not None
        assert lifecycle["timeline"]["days_since_first_seen"] is not None
        assert lifecycle["timeline"]["days_since_first_seen"] >= 0

    def test_recalculate_scores(self):
        """Scores section uses identity.confidence_score."""
        identity = IdentityFactory(confidence_score=0.85)
        lifecycle = LifecycleService.recalculate(identity)

        assert lifecycle["scores"]["confidence"] == 0.85

    def test_recalculate_tags(self):
        """Tags section reflects Identity.tags M2M."""
        identity = IdentityFactory()
        tag1 = TagFactory(name="vip")
        tag2 = TagFactory(name="WH0325")
        identity.tags.add(tag1, tag2)

        lifecycle = LifecycleService.recalculate(identity)

        assert "vip" in lifecycle["tags"]["accumulated"]
        assert "WH0325" in lifecycle["tags"]["accumulated"]
        # "vip" is manual (doesn't match launch pattern), "WH0325" is not
        assert "vip" in lifecycle["tags"]["manual"]
        assert "WH0325" not in lifecycle["tags"]["manual"]

    def test_recalculate_preserves_existing_launch_data(self):
        """Recalculation preserves launches/financial from Phase 4 data."""
        identity = IdentityFactory()
        # Pre-populate with Phase 4 data
        identity.lifecycle_global = {
            "_version": 1,
            "_updated_at": "2026-01-01T00:00:00Z",
            "launches": {
                "total_participated": 2,
                "total_as_buyer": 1,
                "active": ["WH0325"],
                "history": ["WH0125", "WH0325"],
            },
            "financial": {
                "total_spent": 2500.00,
                "currency": "BRL",
            },
        }
        identity.save(update_fields=["lifecycle_global"])

        lifecycle = LifecycleService.recalculate(identity)

        # Launch data preserved
        assert lifecycle["launches"]["total_participated"] == 2
        assert lifecycle["launches"]["active"] == ["WH0325"]
        # Financial data preserved
        assert lifecycle["financial"]["total_spent"] == 2500.00

    def test_recalculate_saves_to_database(self):
        """Recalculation persists the new lifecycle_global to DB."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        identity.refresh_from_db()
        assert identity.lifecycle_global is not None
        assert identity.lifecycle_global["_version"] == LIFECYCLE_SCHEMA_VERSION


# ── Partial Update Tests ─────────────────────────────────────────────


@pytest.mark.django_db
class TestPartialUpdates:
    """Tests for partial section update methods."""

    def test_update_launches_section(self):
        """update_launches_section merges data into launches."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        result = LifecycleService.update_launches_section(
            identity,
            {
                "total_participated": 3,
                "total_as_buyer": 2,
                "active": ["WH0325"],
                "history": ["WH0125", "WH0225", "WH0325"],
                "is_recurrent": True,
            },
        )

        assert result["launches"]["total_participated"] == 3
        assert result["launches"]["is_recurrent"] is True
        assert result["_updated_at"] is not None

    def test_update_financial_section(self):
        """update_financial_section merges financial data and recalculates LTV tier."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        result = LifecycleService.update_financial_section(
            identity,
            {
                "total_spent": 5500.00,
                "net_revenue": 5500.00,
                "average_ticket": 2750.00,
            },
        )

        assert result["financial"]["total_spent"] == 5500.00
        assert result["scores"]["ltv_tier"] == "high"

    def test_update_financial_updates_timeline_purchase_dates(self):
        """Financial update with purchase dates also updates timeline."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        now_iso = timezone.now().isoformat()
        result = LifecycleService.update_financial_section(
            identity,
            {
                "total_spent": 1000.00,
                "first_purchase": now_iso,
                "last_purchase": now_iso,
            },
        )

        assert result["timeline"]["first_purchase"] == now_iso
        assert result["timeline"]["last_purchase"] == now_iso

    def test_update_behavior_section(self):
        """update_behavior_section merges behavior data and syncs scores."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        result = LifecycleService.update_behavior_section(
            identity,
            {
                "pattern": "late_buyer",
                "engagement_score": 0.82,
                "risk_score": 0.15,
            },
        )

        assert result["behavior"]["pattern"] == "late_buyer"
        assert result["scores"]["engagement"] == 0.82
        assert result["scores"]["risk"] == 0.15

    def test_record_entry(self):
        """record_entry increments total_entries and total_form_submissions."""
        identity = IdentityFactory()
        LifecycleService.recalculate(identity)

        LifecycleService.record_entry(identity)
        identity.refresh_from_db()
        assert identity.lifecycle_global["behavior"]["total_entries"] == 1
        assert identity.lifecycle_global["behavior"]["total_form_submissions"] == 1

        LifecycleService.record_entry(identity)
        identity.refresh_from_db()
        assert identity.lifecycle_global["behavior"]["total_entries"] == 2
        assert identity.lifecycle_global["behavior"]["total_form_submissions"] == 2

    def test_partial_update_on_empty_lifecycle(self):
        """Partial update on identity with no lifecycle_global initializes schema first."""
        identity = IdentityFactory()
        identity.lifecycle_global = {}
        identity.save(update_fields=["lifecycle_global"])

        result = LifecycleService.update_launches_section(
            identity,
            {"total_participated": 1},
        )

        assert result["_version"] == LIFECYCLE_SCHEMA_VERSION
        assert result["launches"]["total_participated"] == 1
        # Other sections exist with defaults
        assert "channels" in result
        assert "financial" in result


# ── Schema Forward-Compatibility Tests ───────────────────────────────


class TestSchemaForwardCompatibility:
    """Tests for _ensure_schema_fields."""

    def test_fills_missing_top_level_sections(self):
        """Missing sections are filled with defaults."""
        partial = {
            "_version": 1,
            "channels": {"emails": {"total": 5}},
        }
        result = LifecycleService._ensure_schema_fields(partial)

        assert "timeline" in result
        assert "launches" in result
        assert "financial" in result
        assert "behavior" in result
        assert "tags" in result
        assert "scores" in result

    def test_fills_missing_sub_keys(self):
        """Missing sub-keys within existing sections are filled."""
        partial = {
            "_version": 1,
            "channels": {
                "emails": {"total": 5},
                # phones and fingerprints missing
            },
        }
        result = LifecycleService._ensure_schema_fields(partial)

        assert "phones" in result["channels"]
        assert "fingerprints" in result["channels"]
        # Existing data preserved
        assert result["channels"]["emails"]["total"] == 5

    def test_preserves_existing_data(self):
        """Existing non-default values are not overwritten."""
        data = {
            "_version": 1,
            "financial": {
                "total_spent": 9999.99,
                "currency": "USD",
            },
        }
        result = LifecycleService._ensure_schema_fields(data)

        assert result["financial"]["total_spent"] == 9999.99
        assert result["financial"]["currency"] == "USD"
        # Missing sub-keys filled
        assert "net_revenue" in result["financial"]


# ── LTV Tier Tests ───────────────────────────────────────────────────


class TestLtvTier:
    """Tests for _calculate_ltv_tier."""

    def test_no_purchases(self):
        lifecycle = {"financial": {"total_spent": 0.0}}
        assert LifecycleService._calculate_ltv_tier(lifecycle) is None

    def test_low_tier(self):
        lifecycle = {"financial": {"total_spent": 500.0}}
        assert LifecycleService._calculate_ltv_tier(lifecycle) == "low"

    def test_medium_tier(self):
        lifecycle = {"financial": {"total_spent": 1000.0}}
        assert LifecycleService._calculate_ltv_tier(lifecycle) == "medium"

    def test_medium_tier_upper_bound(self):
        lifecycle = {"financial": {"total_spent": 4999.99}}
        assert LifecycleService._calculate_ltv_tier(lifecycle) == "medium"

    def test_high_tier(self):
        lifecycle = {"financial": {"total_spent": 5000.0}}
        assert LifecycleService._calculate_ltv_tier(lifecycle) == "high"

    def test_missing_financial(self):
        lifecycle = {}
        assert LifecycleService._calculate_ltv_tier(lifecycle) is None


# ── Expand-On-Demand Tests ───────────────────────────────────────────


@pytest.mark.django_db
class TestExpandedData:
    """Tests for get_expanded_data."""

    def test_returns_all_sections(self):
        identity = IdentityFactory()
        data = LifecycleService.get_expanded_data(identity)

        assert "emails" in data
        assert "phones" in data
        assert "fingerprints" in data
        assert "attributions" in data
        assert "lifecycle" in data
        assert "launches" in data

    def test_includes_email_details(self):
        identity = IdentityFactory()
        ContactEmailFactory(
            identity=identity,
            value="test@example.com",
            is_verified=True,
            lifecycle_status="active",
        )

        data = LifecycleService.get_expanded_data(identity)

        assert len(data["emails"]) == 1
        assert data["emails"][0]["value"] == "test@example.com"
        assert data["emails"][0]["is_verified"] is True

    def test_includes_phone_details(self):
        identity = IdentityFactory()
        ContactPhoneFactory(
            identity=identity,
            value="+5511999000099",
            is_whatsapp=True,
        )

        data = LifecycleService.get_expanded_data(identity)

        assert len(data["phones"]) == 1
        assert data["phones"][0]["is_whatsapp"] is True
        assert "display_value" in data["phones"][0]

    def test_launches_placeholder_is_empty(self):
        """Until Phase 4, launches is an empty list."""
        identity = IdentityFactory()
        data = LifecycleService.get_expanded_data(identity)

        assert data["launches"] == []

    def test_lifecycle_defaults_when_empty(self):
        """Returns default schema if lifecycle_global is empty."""
        identity = IdentityFactory()
        identity.lifecycle_global = {}
        identity.save(update_fields=["lifecycle_global"])

        data = LifecycleService.get_expanded_data(identity)

        assert data["lifecycle"]["_version"] == LIFECYCLE_SCHEMA_VERSION


# ── Endpoint Tests ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestExpandEndpoint:
    """Tests for the expand JSON API endpoint."""

    @pytest.fixture
    def staff_user(self):
        """Staff user for lifecycle expansion tests."""
        return UserFactory(email="staff_expand@test.com", staff=True)

    def test_expand_returns_json(self, client, staff_user):
        client.force_login(staff_user)
        identity = IdentityFactory()

        url = reverse("identities:expand", kwargs={"public_id": identity.public_id})
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "phones" in data
        assert "lifecycle" in data

    def test_expand_404_for_missing_identity(self, client, staff_user):
        client.force_login(staff_user)

        url = reverse("identities:expand", kwargs={"public_id": "idt_nonexistent"})
        response = client.get(url)

        assert response.status_code == 404

    def test_expand_requires_auth(self, client):
        identity = IdentityFactory()
        url = reverse("identities:expand", kwargs={"public_id": identity.public_id})
        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302


@pytest.mark.django_db
class TestRecalculateEndpoint:
    """Tests for the recalculate JSON API endpoint."""

    @pytest.fixture
    def staff_user(self):
        """Staff user for lifecycle recalculation tests."""
        return UserFactory(email="staff_recalc@test.com", staff=True)

    def test_recalculate_returns_lifecycle(self, client, staff_user):
        client.force_login(staff_user)
        identity = IdentityFactory()

        url = reverse(
            "identities:recalculate", kwargs={"public_id": identity.public_id}
        )
        response = client.post(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "_version" in data["lifecycle"]

    def test_recalculate_requires_post(self, client, staff_user):
        client.force_login(staff_user)
        identity = IdentityFactory()

        url = reverse(
            "identities:recalculate", kwargs={"public_id": identity.public_id}
        )
        response = client.get(url)

        assert response.status_code == 405

    def test_recalculate_404_for_missing(self, client, staff_user):
        client.force_login(staff_user)

        url = reverse("identities:recalculate", kwargs={"public_id": "idt_nonexistent"})
        response = client.post(url)

        assert response.status_code == 404

    def test_recalculate_requires_auth(self, client):
        identity = IdentityFactory()
        url = reverse(
            "identities:recalculate", kwargs={"public_id": identity.public_id}
        )
        response = client.post(url)

        assert response.status_code == 302

    def test_recalculate_persists_to_db(self, client, staff_user):
        client.force_login(staff_user)
        identity = IdentityFactory()

        url = reverse(
            "identities:recalculate", kwargs={"public_id": identity.public_id}
        )
        client.post(url)

        identity.refresh_from_db()
        assert identity.lifecycle_global is not None
        assert identity.lifecycle_global["_version"] == LIFECYCLE_SCHEMA_VERSION
