"""
Tests for Phase D — Lead Capture.

Tests cover:
- CaptureService.validate_form_data()
- N8NProxyService.build_n8n_payload()
- Campaign fixture loader
- Capture view (GET + POST)
"""
# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.test import RequestFactory
from django.utils import timezone

from apps.landing.campaigns import get_campaign, get_campaign_or_default, _cache
from apps.landing.services.capture import CaptureService
from apps.landing.services.n8n_proxy import N8NProxyService


# ── CaptureService.validate_form_data ────────────────────────────────


class TestCaptureServiceValidation:
    """Test server-side form validation."""

    def test_valid_data_returns_no_errors(self):
        data = {"email": "user@example.com", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert errors == {}

    def test_missing_email_returns_error(self):
        data = {"email": "", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors

    def test_missing_phone_returns_error(self):
        data = {"email": "user@example.com", "phone": ""}
        errors = CaptureService.validate_form_data(data)
        assert "phone" in errors

    def test_both_missing_returns_both_errors(self):
        data = {"email": "", "phone": ""}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors
        assert "phone" in errors

    def test_invalid_email_format(self):
        data = {"email": "not-an-email", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors

    def test_email_too_long(self):
        long_email = "a" * 250 + "@b.com"
        data = {"email": long_email, "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors

    def test_disposable_email_rejected(self):
        data = {"email": "test@guerrillamail.com", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors
        assert "permanente" in errors["email"].lower()

    def test_phone_too_short(self):
        data = {"email": "user@example.com", "phone": "12345"}
        errors = CaptureService.validate_form_data(data)
        assert "phone" in errors

    def test_phone_too_long(self):
        data = {"email": "user@example.com", "phone": "+" + "1" * 20}
        errors = CaptureService.validate_form_data(data)
        assert "phone" in errors

    def test_phone_with_formatting_accepted(self):
        """Phone like '+55 (11) 99988-7766' should be valid (12 digits)."""
        data = {"email": "user@example.com", "phone": "+55 (11) 99988-7766"}
        errors = CaptureService.validate_form_data(data)
        assert errors == {}

    def test_none_values_treated_as_empty(self):
        data = {"email": None, "phone": None}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors
        assert "phone" in errors

    def test_missing_keys_treated_as_empty(self):
        data = {}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors
        assert "phone" in errors

    def test_email_case_insensitive(self):
        data = {"email": "User@Example.COM", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert errors == {}

    def test_email_whitespace_trimmed(self):
        data = {"email": "  user@example.com  ", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert errors == {}

    def test_disposable_yopmail(self):
        data = {"email": "test@yopmail.com", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors

    def test_disposable_mailinator(self):
        data = {"email": "test@mailinator.com", "phone": "+5511999887766"}
        errors = CaptureService.validate_form_data(data)
        assert "email" in errors


# ── N8NProxyService.build_n8n_payload ────────────────────────────────


class TestN8NProxyServicePayload:
    """Test N8N payload builder matches legacy format."""

    def _build_payload(self, **overrides):
        defaults = {
            "email": "user@example.com",
            "phone": "+5511999887766",
            "visitor_id": "fp_abc123",
            "request_id": "req_xyz789",
            "utm_data": {
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "launch-jan",
                "utm_content": "ad-1",
                "utm_term": "investir",
                "utm_id": "gid-123",
            },
            "campaign_config": {
                "slug": "wh-rc-v3",
                "n8n": {
                    "webhook_url": "https://n8n.example.com/webhook/test",
                    "launch_code": "WH0126",
                    "list_id": "424",
                    "form_id": "754ef07d",
                    "form_name": "test form",
                },
            },
            "page_url": "https://example.com/inscrever-wh-rc-v3/",
            "referrer": "https://google.com",
        }
        defaults.update(overrides)
        return N8NProxyService.build_n8n_payload(**defaults)

    def test_email_key_is_legacy_format(self):
        """N8N expects 'E-mail' with capital E and hyphen."""
        payload = self._build_payload()
        assert "E-mail" in payload
        assert payload["E-mail"] == "user@example.com"

    def test_utm_fields_have_cp_suffix(self):
        """UTM fields must have _cp suffix for ActiveCampaign."""
        payload = self._build_payload()
        assert payload["utm_source_cp"] == "google"
        assert payload["utm_medium_cp"] == "cpc"
        assert payload["utm_campaign_cp"] == "launch-jan"
        assert payload["utm_content_cp"] == "ad-1"
        assert payload["utm_term_cp"] == "investir"

    def test_utm_id_no_suffix(self):
        """utm_id does NOT have _cp suffix."""
        payload = self._build_payload()
        assert payload["utm_id"] == "gid-123"

    def test_fingerprint_fields(self):
        payload = self._build_payload()
        assert payload["fingerprint"] == "fp_abc123"
        assert payload["eventid"] == "req_xyz789"

    def test_campaign_identifiers(self):
        payload = self._build_payload()
        assert payload["launch_code"] == "WH0126"
        assert payload["list"] == "424"
        assert payload["form_id"] == "754ef07d"
        assert payload["form_name"] == "test form"

    def test_origin_tracking(self):
        payload = self._build_payload()
        assert payload["origem_lead_cp"] == "https://example.com/inscrever-wh-rc-v3/"
        assert payload["origem_lead_history_1"] == "https://google.com"

    def test_versao_page_from_slug(self):
        payload = self._build_payload()
        assert payload["versao_page_cp"] == "wh-rc-v3"

    def test_timestamp_present(self):
        payload = self._build_payload()
        assert "timestamp" in payload
        assert len(payload["timestamp"]) > 0

    def test_phone_field(self):
        payload = self._build_payload()
        assert payload["phone"] == "+5511999887766"

    def test_empty_utm_data(self):
        payload = self._build_payload(
            utm_data={
                "utm_source": "",
                "utm_medium": "",
                "utm_campaign": "",
                "utm_content": "",
                "utm_term": "",
                "utm_id": "",
            }
        )
        assert payload["utm_source_cp"] == ""
        assert payload["utm_medium_cp"] == ""

    def test_missing_n8n_config_defaults(self):
        payload = self._build_payload(campaign_config={"slug": "test", "n8n": {}})
        assert payload["launch_code"] == ""
        assert payload["list"] == ""


# ── N8NProxyService.send_to_n8n ─────────────────────────────────────


class TestN8NProxyServiceSend:
    """Test N8N webhook sending with retry logic."""

    def test_empty_url_returns_false(self):
        result = N8NProxyService.send_to_n8n("", {"test": "data"})
        assert result is False

    @patch("apps.landing.services.n8n_proxy.httpx.Client")
    def test_successful_send(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = N8NProxyService.send_to_n8n(
            "https://n8n.example.com/webhook/test",
            {"E-mail": "test@example.com"},
        )
        assert result is True
        mock_client.post.assert_called_once()

    @patch("apps.landing.services.n8n_proxy.httpx.Client")
    def test_retries_on_failure(self, mock_client_cls):
        import httpx

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = N8NProxyService.send_to_n8n(
            "https://n8n.example.com/webhook/test",
            {"E-mail": "test@example.com"},
            max_retries=2,
        )
        assert result is False
        assert mock_client.post.call_count == 2


# ── Campaign Fixture Loader ──────────────────────────────────────────


class TestCampaignLoader:
    """Test campaign JSON fixture loading."""

    def setup_method(self):
        """Clear cache before each test."""
        _cache.clear()

    def test_load_existing_campaign(self):
        campaign = get_campaign("wh-rc-v3")
        assert campaign is not None
        assert campaign["slug"] == "wh-rc-v3"
        assert "n8n" in campaign
        assert "headline" in campaign

    def test_load_nonexistent_campaign_returns_none(self):
        campaign = get_campaign("nonexistent-campaign-xyz")
        assert campaign is None

    def test_get_campaign_or_default_existing(self):
        campaign = get_campaign_or_default("wh-rc-v3")
        assert campaign["slug"] == "wh-rc-v3"
        assert campaign["n8n"]["launch_code"] == "WH0126"

    def test_get_campaign_or_default_fallback(self):
        campaign = get_campaign_or_default("unknown-slug")
        assert campaign["slug"] == "unknown-slug"
        assert "form" in campaign
        assert "headline" in campaign
        assert campaign["n8n"]["webhook_url"] == ""

    def test_campaign_cached_on_second_load(self):
        """Second load should come from cache."""
        c1 = get_campaign("wh-rc-v3")
        c2 = get_campaign("wh-rc-v3")
        assert c1 is c2  # Same object reference = cached

    def test_campaign_has_required_fields(self):
        campaign = get_campaign("wh-rc-v3")
        assert campaign is not None
        required_keys = ["slug", "meta", "headline", "badges", "form", "n8n"]
        for key in required_keys:
            assert key in campaign, f"Missing required key: {key}"

    def test_campaign_n8n_config(self):
        campaign = get_campaign("wh-rc-v3")
        assert campaign is not None
        n8n = campaign["n8n"]
        assert "webhook_url" in n8n
        assert "launch_code" in n8n
        assert "list_id" in n8n
        assert "form_id" in n8n


# ── Capture View ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCaptureView:
    """Test the capture_page view (GET and POST)."""

    def setup_method(self):
        self.rf = RequestFactory()
        _cache.clear()

    def _make_get_request(self, slug="wh-rc-v3"):
        from apps.landing.views import capture_page

        request = self.rf.get(f"/inscrever-{slug}/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}
        return capture_page(request, slug)

    def test_get_returns_200(self):
        """GET /inscrever-<slug>/ should return 200."""
        response = self._make_get_request()
        assert response.status_code == 200

    def test_get_returns_inertia_response(self):
        """GET should return an Inertia response with campaign props."""
        response = self._make_get_request()
        # Inertia responses have the X-Inertia header
        assert response.get("X-Inertia") == "true"
        body = json.loads(response.content)
        assert body["component"] == "Capture/Index"
        assert "campaign" in body["props"]
        assert "capture_token" in body["props"]

    def test_get_db_backed_page_includes_capture_page_public_id(self):
        """DB-backed landings should expose capture_page_public_id to the frontend."""
        from apps.landing.views import capture_page
        from tests.factories import CapturePageFactory

        page = CapturePageFactory(slug="db-backed-capture")

        request = self.rf.get("/inscrever-db-backed-capture/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}

        response = capture_page(request, "db-backed-capture")

        assert response.status_code == 200
        body = json.loads(response.content)
        assert body["props"]["capture_page_public_id"] == page.public_id

    def test_get_unknown_slug_redirects_to_default(self):
        """GET with unknown slug should redirect to default campaign."""
        from apps.landing.views import capture_page

        request = self.rf.get("/inscrever-unknown-thing/")
        request.session = {}
        request.data = {}

        response = capture_page(request, "unknown-thing")
        assert response.status_code == 302
        assert "/inscrever-wh-rc-v3/" in response.url

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_get_db_backed_capture_page_still_renders_without_json_fallback(self):
        from apps.landing.views import capture_page
        from tests.factories import CapturePageFactory

        CapturePageFactory(slug="db-only-capture")

        request = self.rf.get("/inscrever-db-only-capture/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}

        response = capture_page(request, "db-only-capture")

        assert response.status_code == 200

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_get_default_capture_page_returns_404_without_db_when_json_fallback_disabled(
        self,
    ):
        from apps.landing.views import capture_page

        request = self.rf.get("/inscrever-wh-rc-v3/")
        request.session = {}
        request.data = {}

        response = capture_page(request, "wh-rc-v3")

        assert response.status_code == 404

    def test_post_valid_data_redirects(self):
        """POST with valid data should redirect to thank-you page."""
        from apps.landing.models import LeadIntegrationOutbox
        from apps.landing.views import capture_page

        request = self.rf.post(
            "/inscrever-wh-rc-v3/",
            content_type="application/json",
        )
        request.session = {}
        request.data = {
            "email": "test@example.com",
            "phone": "+5511999887766",
            "visitor_id": "fp_test123",
            "request_id": "req_test456",
        }

        with patch("apps.landing.views.CaptureService.process_lead") as mock_process:
            mock_process.return_value = {
                "resolution": {},
                "identity": None,
                "identity_id": "ident_abc123",
                "is_new": True,
                "n8n_payload": {"E-mail": "test@example.com"},
                "n8n_webhook_url": "https://n8n.example.com/webhook/test",
            }
            with patch(
                "apps.landing.tasks.process_lead_integration_outbox_task"
            ) as mock_task:
                response = capture_page(request, "wh-rc-v3")

                assert response.status_code == 302
                assert "/obrigado-wh-rc-v3/" in response.url
                assert (
                    LeadIntegrationOutbox.objects.filter(
                        integration_type=LeadIntegrationOutbox.IntegrationType.N8N
                    ).count()
                    == 1
                )

    def test_post_json_fallback_materializes_page_and_creates_submission(self):
        """Valid submit on JSON fallback should still create CaptureSubmission."""
        from apps.ads.models import AdProvider, CaptureSubmission
        from apps.landing.views import capture_page
        from tests.factories import IdentityFactory

        AdProvider.objects.create(
            code="direct",
            name="Direto",
            source_patterns={
                "utm_source_patterns": [],
                "vk_source_values": [],
                "click_id_param": "",
            },
            naming_convention={},
        )

        request = self.rf.post(
            "/inscrever-wh-rc-v3/",
            content_type="application/json",
        )
        request.session = {}
        request.data = {
            "email": "lead-json@example.com",
            "phone": "+5511999887766",
            "visitor_id": "fp_json_test",
            "request_id": "req_json_test",
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "utm_id": "",
            "fbclid": "",
            "vk_ad_id": "",
            "vk_source": "",
        }
        request.client_ip = None
        request.geo_data = {}
        request.device_data = None
        request.device_profile = None
        request.META["HTTP_USER_AGENT"] = "pytest"

        identity = IdentityFactory()

        with patch("apps.landing.views.CaptureService.process_lead") as mock_process:
            mock_process.return_value = {
                "resolution": {},
                "identity": identity,
                "identity_id": identity.public_id,
                "is_new": True,
                "n8n_payload": {},
                "n8n_webhook_url": "",
            }

            response = capture_page(request, "wh-rc-v3")

        assert response.status_code == 302
        assert "/obrigado-wh-rc-v3/" in response.url

        submission = CaptureSubmission.objects.get(email_raw="lead-json@example.com")
        assert submission.capture_page.slug == "wh-rc-v3"
        assert submission.identity == identity

    def test_post_replay_is_idempotent(self):
        """A repeated valid submit with the same logical key should not duplicate side effects."""
        from apps.ads.models import CaptureSubmission
        from apps.landing.models import LeadCaptureIdempotencyKey, LeadIntegrationOutbox
        from apps.landing.views import capture_page
        from core.tracking.models import CaptureEvent
        from tests.factories import CapturePageFactory, IdentityFactory

        page = CapturePageFactory(slug="idempotent-capture")
        identity = IdentityFactory()

        payload = {
            "email": "idempotent@example.com",
            "phone": "+5511999777666",
            "visitor_id": "fp_idempotent",
            "request_id": "req_idempotent",
            "capture_token": "44444444-4444-4444-8444-444444444444",
            "capture_page_public_id": page.public_id,
        }

        def make_request():
            request = self.rf.post(
                "/inscrever-idempotent-capture/",
                content_type="application/json",
            )
            request.session = {
                "capture_slug": page.slug,
                "last_page": f"/inscrever-{page.slug}/",
            }
            request.data = dict(payload)
            request.client_ip = None
            request.geo_data = {}
            request.device_data = None
            request.device_profile = None
            request.META["HTTP_USER_AGENT"] = "pytest"
            return request

        with patch("apps.landing.views.CaptureService.process_lead") as mock_process:
            mock_process.return_value = {
                "resolution": {},
                "identity": identity,
                "identity_id": identity.public_id,
                "is_new": True,
                "n8n_payload": {"E-mail": "idempotent@example.com"},
                "n8n_webhook_url": "https://n8n.example.com/webhook/test",
            }

            response1 = capture_page(make_request(), page.slug)
            response2 = capture_page(make_request(), page.slug)

        assert response1.status_code == 302
        assert response2.status_code == 302
        assert response1.url == response2.url
        assert mock_process.call_count == 1
        assert (
            CaptureSubmission.objects.filter(email_raw="idempotent@example.com").count()
            == 1
        )
        assert (
            CaptureEvent.objects.filter(
                event_type=CaptureEvent.EventType.FORM_SUCCESS,
                capture_token=payload["capture_token"],
            ).count()
            == 1
        )
        assert LeadIntegrationOutbox.objects.count() == 1
        assert LeadCaptureIdempotencyKey.objects.count() == 1

    def test_post_invalid_data_returns_errors(self):
        """POST with empty data should re-render with errors."""
        from apps.landing.views import capture_page

        request = self.rf.post(
            "/inscrever-wh-rc-v3/",
            content_type="application/json",
        )
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {"email": "", "phone": ""}

        response = capture_page(request, "wh-rc-v3")
        # Should re-render the page (200) with errors, not redirect
        assert response.status_code == 200
        body = json.loads(response.content)
        assert "errors" in body["props"]
        assert "email" in body["props"]["errors"]
        assert "phone" in body["props"]["errors"]

    def test_post_disposable_email_returns_error(self):
        """POST with disposable email should return validation error."""
        from apps.landing.views import capture_page

        request = self.rf.post(
            "/inscrever-wh-rc-v3/",
            content_type="application/json",
        )
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {
            "email": "test@guerrillamail.com",
            "phone": "+5511999887766",
        }

        response = capture_page(request, "wh-rc-v3")
        assert response.status_code == 200
        body = json.loads(response.content)
        assert "email" in body["props"]["errors"]


@pytest.mark.django_db
class TestCaptureIntentView:
    """Tests for the capture-intent prelead endpoint."""

    def setup_method(self):
        self.rf = RequestFactory()
        _cache.clear()

    def test_capture_intent_creates_prelead_without_contact_channels(self):
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.phone.models import ContactPhone
        from apps.landing.views import capture_intent
        from core.tracking.models import CaptureIntent
        from tests.factories import CapturePageFactory, IdentityFactory

        identity = IdentityFactory(confidence_score=0.05)
        identity.refresh_from_db()
        initial_confidence = identity.confidence_score
        page = CapturePageFactory(slug="intent-test-page")
        payload = {
            "email_hint": "prelead@example.com",
            "phone_hint": "+5511999887766",
            "capture_token": "11111111-1111-4111-8111-111111111111",
            "visitor_id": "fp_intent_123",
            "request_id": "req_intent_456",
        }

        request = self.rf.post(
            "/api/capture-intent/",
            data=json.dumps(payload),
            content_type="text/plain",
        )
        request.session = {
            "capture_slug": page.slug,
            "last_page": f"/inscrever-{page.slug}/",
            "identity_pk": identity.pk,
        }
        request.identity = identity
        request.fingerprint_identity = None
        request.visitor_id = "fp_intent_123"
        request.META["HTTP_REFERER"] = f"http://testserver/inscrever-{page.slug}/"

        response = capture_intent(request)

        assert response.status_code == 202
        body = json.loads(response.content)
        assert body["status"] == "ok"
        assert body["intent_created"] is True

        intent = CaptureIntent.objects.get(capture_token=payload["capture_token"])
        assert intent.identity == identity
        assert intent.capture_page == page
        assert intent.email_hint == "prelead@example.com"
        assert intent.phone_hint == "+5511999887766"
        assert intent.visitor_id == "fp_intent_123"
        assert intent.request_id == "req_intent_456"
        assert intent.status == CaptureIntent.Status.PENDING

        assert ContactEmail.objects.count() == 0
        assert ContactPhone.objects.count() == 0
        identity.refresh_from_db()
        assert identity.confidence_score == initial_confidence

    def test_capture_intent_submit_marks_prelead_completed(self):
        from apps.landing.views import capture_page
        from core.tracking.models import CaptureIntent
        from tests.factories import CapturePageFactory, IdentityFactory

        identity = IdentityFactory()
        page = CapturePageFactory(slug="complete-intent-page")
        intent = CaptureIntent.objects.create(
            capture_token="22222222-2222-4222-8222-222222222222",
            page_path=f"/inscrever-{page.slug}/",
            capture_page=page,
            identity=identity,
            email_hint="complete@example.com",
            phone_hint="+5511999000111",
        )

        request = self.rf.post(
            f"/inscrever-{page.slug}/",
            content_type="application/json",
        )
        request.session = {
            "capture_slug": page.slug,
            "last_page": f"/inscrever-{page.slug}/",
        }
        request.data = {
            "email": "complete@example.com",
            "phone": "+5511999000111",
            "capture_token": str(intent.capture_token),
            "capture_page_public_id": page.public_id,
            "visitor_id": "",
            "request_id": "",
        }
        request.client_ip = None
        request.geo_data = {}
        request.device_data = None
        request.device_profile = None
        request.META["HTTP_USER_AGENT"] = "pytest"

        with patch("apps.landing.views.CaptureService.process_lead") as mock_process:
            mock_process.return_value = {
                "resolution": {},
                "identity": identity,
                "identity_id": identity.public_id,
                "is_new": False,
                "n8n_payload": {},
                "n8n_webhook_url": "",
            }
            with patch(
                "apps.landing.views._create_capture_submission", return_value=None
            ):
                response = capture_page(request, page.slug)

        assert response.status_code == 302
        intent.refresh_from_db()
        assert intent.status == CaptureIntent.Status.COMPLETED
        assert intent.completed_at is not None


@pytest.mark.django_db
class TestLeadIntegrationOutbox:
    """Tests for the durable outbox processor."""

    def test_process_n8n_outbox_marks_sent(self):
        from apps.landing.models import LeadIntegrationOutbox
        from apps.landing.tasks import process_lead_integration_outbox_task
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory(n8n_status="pending")
        outbox = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="33333333-3333-4333-8333-333333333333",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            payload={
                "webhook_url": "https://n8n.example.com/webhook/test",
                "payload": {"E-mail": "lead@example.com"},
                "submission_id": submission.public_id,
            },
        )

        with patch(
            "apps.landing.tasks.N8NProxyService.send_to_n8n",
            return_value=True,
        ) as mock_send:
            result = process_lead_integration_outbox_task.run(outbox.public_id)

        assert result is True
        mock_send.assert_called_once()
        outbox.refresh_from_db()
        submission.refresh_from_db()
        assert outbox.status == LeadIntegrationOutbox.Status.SENT
        assert outbox.processed_at is not None
        assert outbox.attempts == 1
        assert submission.n8n_status == "sent"

    def test_process_n8n_outbox_marks_failed_on_permanent_failure(self):
        from apps.landing.models import LeadIntegrationOutbox
        from apps.landing.tasks import process_lead_integration_outbox_task
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory(n8n_status="pending")
        outbox = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="34333333-3333-4333-8333-333333333333",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            payload={
                "webhook_url": "https://n8n.example.com/webhook/test",
                "payload": {"E-mail": "lead@example.com"},
                "submission_id": submission.public_id,
            },
        )

        original_retries = process_lead_integration_outbox_task.request.retries
        try:
            process_lead_integration_outbox_task.request.retries = (
                process_lead_integration_outbox_task.max_retries
            )
            with patch(
                "apps.landing.tasks.N8NProxyService.send_to_n8n",
                side_effect=RuntimeError("n8n down"),
            ):
                result = process_lead_integration_outbox_task.run(outbox.public_id)
        finally:
            process_lead_integration_outbox_task.request.retries = original_retries

        assert result is False
        outbox.refresh_from_db()
        submission.refresh_from_db()
        assert outbox.status == LeadIntegrationOutbox.Status.FAILED
        assert outbox.processed_at is not None
        assert outbox.last_error == "n8n down"
        assert submission.n8n_status == "failed"


@pytest.mark.django_db
class TestRequeueLeadIntegrationsCommand:
    def test_requeue_failed_integrations_requeues_matching_entries(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        failed_n8n = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="55555555-5555-4555-8555-555555555555",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            status=LeadIntegrationOutbox.Status.FAILED,
            last_error="boom",
        )
        sent_meta = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="66666666-6666-4666-8666-666666666666",
            integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
            status=LeadIntegrationOutbox.Status.SENT,
        )

        with patch(
            "apps.landing.management.commands.requeue_failed_lead_integrations.process_lead_integration_outbox_task"
        ) as mock_task:
            call_command("requeue_failed_lead_integrations")

        failed_n8n.refresh_from_db()
        sent_meta.refresh_from_db()

        assert failed_n8n.status == LeadIntegrationOutbox.Status.PENDING
        assert failed_n8n.last_error == ""
        assert failed_n8n.processed_at is None
        assert sent_meta.status == LeadIntegrationOutbox.Status.SENT
        mock_task.delay.assert_called_once_with(failed_n8n.public_id)

    def test_requeue_failed_integrations_dry_run_does_not_mutate(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        failed_n8n = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="77777777-7777-4777-8777-777777777777",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            status=LeadIntegrationOutbox.Status.FAILED,
            last_error="boom",
        )

        with patch(
            "apps.landing.management.commands.requeue_failed_lead_integrations.process_lead_integration_outbox_task"
        ) as mock_task:
            call_command("requeue_failed_lead_integrations", "--dry-run")

        failed_n8n.refresh_from_db()
        assert failed_n8n.status == LeadIntegrationOutbox.Status.FAILED
        assert failed_n8n.last_error == "boom"
        mock_task.delay.assert_not_called()

    def test_requeue_failed_integrations_filters_by_outbox_id(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        first = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="88888888-8888-4888-8888-888888888888",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            status=LeadIntegrationOutbox.Status.FAILED,
        )
        second = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="99999999-9999-4999-8999-999999999999",
            integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
            status=LeadIntegrationOutbox.Status.FAILED,
        )

        with patch(
            "apps.landing.management.commands.requeue_failed_lead_integrations.process_lead_integration_outbox_task"
        ) as mock_task:
            call_command(
                "requeue_failed_lead_integrations",
                "--outbox-id",
                first.public_id,
            )

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.status == LeadIntegrationOutbox.Status.PENDING
        assert second.status == LeadIntegrationOutbox.Status.FAILED
        mock_task.delay.assert_called_once_with(first.public_id)


@pytest.mark.django_db
class TestLeadIntegrationHealth:
    def test_health_check_passes_when_outbox_is_healthy(self):
        from apps.landing.services.outbox import LeadIntegrationOutboxMonitoringService

        snapshot = LeadIntegrationOutboxMonitoringService.get_health_snapshot(
            failed_threshold=1,
            pending_threshold=1,
            pending_max_age_minutes=1,
        )

        assert snapshot["healthy"] is True
        call_command(
            "check_lead_integration_health",
            "--failed-threshold",
            "1",
            "--pending-threshold",
            "1",
            "--pending-max-age-minutes",
            "1",
        )

    def test_health_check_fails_when_failed_threshold_is_breached(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            status=LeadIntegrationOutbox.Status.FAILED,
        )

        with pytest.raises(CommandError):
            call_command(
                "check_lead_integration_health",
                "--failed-threshold",
                "1",
            )

    def test_health_snapshot_flags_overdue_integrations_by_type(self):
        from apps.landing.models import LeadIntegrationOutbox
        from apps.landing.services.outbox import LeadIntegrationOutboxMonitoringService
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        old_n8n = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            status=LeadIntegrationOutbox.Status.PENDING,
        )
        old_meta = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="ffffffff-ffff-4fff-8fff-ffffffffffff",
            integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
            status=LeadIntegrationOutbox.Status.PENDING,
        )
        LeadIntegrationOutbox.objects.filter(pk=old_n8n.pk).update(
            created_at=timezone.now() - timezone.timedelta(minutes=11)
        )
        LeadIntegrationOutbox.objects.filter(pk=old_meta.pk).update(
            created_at=timezone.now() - timezone.timedelta(minutes=16)
        )

        snapshot = LeadIntegrationOutboxMonitoringService.get_health_snapshot(
            failed_threshold=99,
            pending_threshold=99,
            pending_max_age_minutes=99,
        )

        assert snapshot["healthy"] is False
        assert snapshot["n8n_overdue_count"] == 1
        assert snapshot["meta_capi_overdue_count"] == 1


@pytest.mark.django_db
class TestCaptureTransactionRollback:
    def test_complete_capture_rolls_back_if_form_success_event_fails(self):
        from apps.landing.models import LeadCaptureIdempotencyKey, LeadIntegrationOutbox
        from apps.landing.services.capture import CaptureService
        from core.tracking.models import CaptureEvent
        from tests.factories import CapturePageFactory, IdentityFactory

        identity = IdentityFactory()
        page = CapturePageFactory(slug="rollback-capture")

        request = RequestFactory().post(
            "/inscrever-rollback-capture/",
            content_type="application/json",
        )
        request.session = {
            "capture_slug": page.slug,
            "last_page": f"/inscrever-{page.slug}/",
        }
        request.client_ip = None
        request.geo_data = {}
        request.device_data = None
        request.device_profile = None
        request.META["HTTP_USER_AGENT"] = "pytest"

        data = {
            "email": "rollback@example.com",
            "phone": "+5511999887766",
            "capture_token": "12121212-1212-4212-8212-121212121212",
            "request_id": "req_rollback",
            "visitor_id": "fp_rollback",
        }
        backend_config = {
            "slug": page.slug,
            "form": {"thank_you_url": f"/obrigado-{page.slug}/"},
            "n8n": {"webhook_url": "https://n8n.example.com/webhook/test"},
        }

        with patch.object(
            CaptureService,
            "process_lead",
            return_value={
                "resolution": {},
                "identity": identity,
                "identity_id": identity.public_id,
                "is_new": True,
                "n8n_payload": {"E-mail": "rollback@example.com"},
                "n8n_webhook_url": "https://n8n.example.com/webhook/test",
            },
        ):
            with patch(
                "apps.landing.services.capture.TrackingService.create_event",
                side_effect=RuntimeError("event insert failed"),
            ):
                with pytest.raises(RuntimeError, match="event insert failed"):
                    CaptureService.complete_capture(
                        request=request,
                        data=data,
                        backend_config=backend_config,
                        campaign_slug=page.slug,
                        capture_token=data["capture_token"],
                        capture_page_model=page,
                        t_start=0.0,
                    )

        assert LeadCaptureIdempotencyKey.objects.count() == 0
        assert LeadIntegrationOutbox.objects.count() == 0
        assert (
            CaptureEvent.objects.filter(
                event_type=CaptureEvent.EventType.FORM_SUCCESS,
                capture_token=data["capture_token"],
            ).count()
            == 0
        )


@pytest.mark.django_db
class TestRepairLeadIntegrationPayloadsCommand:
    def test_repair_n8n_payload_backfills_submission_id_and_identity(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        outbox = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            payload={
                "webhook_url": "https://n8n.example.com/webhook/test",
                "payload": {},
            },
            identity_public_id="",
        )

        call_command("repair_lead_integration_payloads")

        outbox.refresh_from_db()
        assert outbox.identity_public_id == submission.identity.public_id
        assert outbox.payload["submission_id"] == submission.public_id

    def test_repair_meta_payload_backfills_hashes_and_external_id(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory(
            email_raw="repair@example.com", phone_raw="+5511999555000"
        )
        outbox = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            integration_type=LeadIntegrationOutbox.IntegrationType.META_CAPI,
            payload={},
            identity_public_id="",
        )

        call_command(
            "repair_lead_integration_payloads", "--integration-type", "meta_capi"
        )

        outbox.refresh_from_db()
        assert outbox.identity_public_id == submission.identity.public_id
        assert outbox.payload["external_id"] == submission.identity.public_id
        assert outbox.payload["email_hash"]
        assert outbox.payload["phone_hash"]
        assert outbox.payload["event_id"] == str(submission.capture_token)

    def test_repair_payloads_dry_run_does_not_mutate(self):
        from apps.landing.models import LeadIntegrationOutbox
        from tests.factories import CaptureSubmissionFactory

        submission = CaptureSubmissionFactory()
        outbox = LeadIntegrationOutbox.objects.create(
            capture_submission=submission,
            capture_token="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            integration_type=LeadIntegrationOutbox.IntegrationType.N8N,
            payload={
                "webhook_url": "https://n8n.example.com/webhook/test",
                "payload": {},
            },
            identity_public_id="",
        )

        call_command("repair_lead_integration_payloads", "--dry-run")

        outbox.refresh_from_db()
        assert outbox.identity_public_id == ""
        assert "submission_id" not in outbox.payload


# ── Thank You View ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestThankYouView:
    """Test the thank_you_page view."""

    def setup_method(self):
        self.rf = RequestFactory()
        _cache.clear()

    def test_get_returns_200(self):
        from apps.landing.views import thank_you_page

        request = self.rf.get("/obrigado-wh-rc-v3/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}

        response = thank_you_page(request, "wh-rc-v3")
        assert response.status_code == 200

    def test_get_returns_inertia_response(self):
        from apps.landing.views import thank_you_page

        request = self.rf.get("/obrigado-wh-rc-v3/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}

        response = thank_you_page(request, "wh-rc-v3")
        body = json.loads(response.content)
        assert body["component"] == "ThankYou/Index"
        assert "campaign" in body["props"]


@pytest.mark.django_db
class TestSpecialLandingFlows:
    def setup_method(self):
        self.rf = RequestFactory()
        _cache.clear()

    @override_settings(LANDING_JSON_FALLBACK_ENABLED=False)
    def test_agrelliflix_remains_available_as_explicit_special_flow(self):
        from apps.landing.views import agrelliflix_page

        request = self.rf.get("/agrelliflix/")
        request.session = {}
        request.META["HTTP_X_INERTIA"] = "true"
        request.data = {}

        response = agrelliflix_page(request)

        assert response.status_code == 200
        body = json.loads(response.content)
        assert body["component"] == "AgreliFlix/Index"
