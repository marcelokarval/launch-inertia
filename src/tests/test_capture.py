"""
Tests for Phase D — Lead Capture.

Tests cover:
- CaptureService.validate_form_data()
- N8NProxyService.build_n8n_payload()
- Campaign fixture loader
- Capture view (GET + POST)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

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
        assert "fingerprint_api_key" in body["props"]

    def test_get_unknown_slug_redirects_to_default(self):
        """GET with unknown slug should redirect to default campaign."""
        from apps.landing.views import capture_page

        request = self.rf.get("/inscrever-unknown-thing/")
        request.session = {}
        request.data = {}

        response = capture_page(request, "unknown-thing")
        assert response.status_code == 302
        assert "/inscrever-wh-rc-v3/" in response.url

    def test_post_valid_data_redirects(self):
        """POST with valid data should redirect to thank-you page."""
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
                "identity_id": "ident_abc123",
                "is_new": True,
                "n8n_payload": {"E-mail": "test@example.com"},
                "n8n_webhook_url": "https://n8n.example.com/webhook/test",
            }
            with patch("apps.landing.views.send_to_n8n_task") as mock_task:
                response = capture_page(request, "wh-rc-v3")

                assert response.status_code == 302
                assert "/obrigado-wh-rc-v3/" in response.url
                mock_task.delay.assert_called_once()

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
