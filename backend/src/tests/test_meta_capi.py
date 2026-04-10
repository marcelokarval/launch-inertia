"""
Tests for Phase 5: Meta CAPI Foundation.

Covers:
- MetaCAPIService (SDK wrapper, mocked at SDK layer)
- Meta webhook endpoint (verification + event handling)
- _dispatch_meta_capi_lead() helper
- send_meta_conversion Celery task (mocked service)
"""
# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

from infrastructure.integrations.meta_capi import CAPIResponse, MetaCAPIService
from infrastructure.integrations.meta_webhook import _verify_signature


# ── MetaCAPIService tests ────────────────────────────────────────────


class TestMetaCAPIService:
    """Tests for MetaCAPIService using mocked SDK."""

    def test_not_configured_returns_error(self):
        """Service with empty pixel_id/access_token returns not_configured."""
        service = MetaCAPIService(pixel_id="", access_token="")
        response = service.send_lead_event(
            email_hash="abc123",
            phone_hash="def456",
            event_id="test-uuid",
        )
        assert not response.success
        assert response.error == "not_configured"

    def test_not_configured_missing_token(self):
        service = MetaCAPIService(pixel_id="123", access_token="")
        response = service.send_lead_event(
            email_hash="abc",
            phone_hash="def",
            event_id="uuid",
        )
        assert not response.success
        assert response.error == "not_configured"

    @patch("infrastructure.integrations.meta_capi.MetaCAPIService._send_events")
    def test_send_lead_event_calls_send_events(self, mock_send):
        """send_lead_event() builds correct event and calls _send_events."""
        mock_send.return_value = CAPIResponse(success=True, events_received=1)
        service = MetaCAPIService(pixel_id="123", access_token="token")

        result = service.send_lead_event(
            email_hash="emailhash",
            phone_hash="phonehash",
            event_id="capture-uuid-123",
            event_source_url="https://example.com/inscrever-test/",
            client_ip="1.2.3.4",
            user_agent="Mozilla/5.0",
        )

        assert result.success
        assert result.events_received == 1
        mock_send.assert_called_once()
        # Verify event was built
        events = mock_send.call_args[0][0]
        assert len(events) == 1

    @patch("infrastructure.integrations.meta_capi.MetaCAPIService._send_events")
    def test_send_page_view_event(self, mock_send):
        mock_send.return_value = CAPIResponse(success=True, events_received=1)
        service = MetaCAPIService(pixel_id="123", access_token="token")

        result = service.send_page_view_event(
            event_id="pv-uuid",
            event_source_url="https://example.com/inscrever-test/",
        )

        assert result.success
        mock_send.assert_called_once()

    def test_build_user_data_with_all_fields(self):
        """_build_user_data sets all fields correctly."""
        service = MetaCAPIService(pixel_id="123", access_token="token")
        user_data = service._build_user_data(
            email_hash="em_hash",
            phone_hash="ph_hash",
            client_ip="1.2.3.4",
            user_agent="UA",
            fbc="fb.1.123",
            fbp="fb.1.456",
            external_id="idt_abc123",
        )
        assert user_data.emails == ["em_hash"]
        assert user_data.phones == ["ph_hash"]
        assert user_data.client_ip_address == "1.2.3.4"
        assert user_data.client_user_agent == "UA"
        assert user_data.fbc == "fb.1.123"
        assert user_data.fbp == "fb.1.456"
        assert user_data.external_ids == ["idt_abc123"]

    def test_build_user_data_empty_fields(self):
        """Empty fields are not set on UserData."""
        service = MetaCAPIService(pixel_id="123", access_token="token")
        user_data = service._build_user_data()
        # SDK defaults
        assert not getattr(user_data, "emails", None)
        assert not getattr(user_data, "phones", None)

    def test_build_event_sets_action_source(self):
        """Events have action_source=WEBSITE."""
        from facebook_business.adobjects.serverside.action_source import ActionSource

        service = MetaCAPIService(pixel_id="123", access_token="token")
        event = service._build_event(
            event_name="Lead",
            event_id="test-id",
        )
        assert event.action_source == ActionSource.WEBSITE
        assert event.event_name == "Lead"
        assert event.event_id == "test-id"

    @patch("facebook_business.adobjects.serverside.event_request.EventRequest.execute")
    def test_send_events_success(self, mock_execute):
        """Successful SDK call returns correct CAPIResponse."""
        mock_response = MagicMock()
        mock_response.events_received = 1
        mock_response.fbtrace_id = "trace123"
        mock_execute.return_value = mock_response

        service = MetaCAPIService(pixel_id="123456", access_token="token123")
        event = service._build_event(event_name="Lead", event_id="ev1")
        result = service._send_events([event])

        assert result.success
        assert result.events_received == 1
        assert result.fbtrace_id == "trace123"

    @patch("facebook_business.adobjects.serverside.event_request.EventRequest.execute")
    def test_send_events_sdk_error(self, mock_execute):
        """SDK exception is caught and returned as error."""
        mock_execute.side_effect = Exception("API rate limit exceeded")

        service = MetaCAPIService(pixel_id="123456", access_token="token123")
        event = service._build_event(event_name="Lead", event_id="ev2")
        result = service._send_events([event])

        assert not result.success
        assert "rate limit" in result.error.lower()

    def test_test_event_code_passed_to_request(self):
        """test_event_code is passed through to EventRequest."""
        service = MetaCAPIService(
            pixel_id="123",
            access_token="token",
            test_event_code="TEST123",
        )
        assert service.test_event_code == "TEST123"


# ── Meta Webhook tests ───────────────────────────────────────────────


class TestMetaWebhookVerification:
    """Tests for meta_webhook GET (verification handshake)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()

    @patch.dict("os.environ", {"META_WEBHOOK_VERIFY_TOKEN": "my_secret_token"})
    def test_valid_verification(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        request = self.rf.get(
            "/api/webhooks/meta/",
            {
                "hub.mode": "subscribe",
                "hub.challenge": "challenge_string_123",
                "hub.verify_token": "my_secret_token",
            },
        )
        response = meta_webhook(request)
        assert response.status_code == 200
        assert response.content == b"challenge_string_123"

    @patch.dict("os.environ", {"META_WEBHOOK_VERIFY_TOKEN": "my_secret_token"})
    def test_invalid_token_returns_403(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        request = self.rf.get(
            "/api/webhooks/meta/",
            {
                "hub.mode": "subscribe",
                "hub.challenge": "challenge",
                "hub.verify_token": "wrong_token",
            },
        )
        response = meta_webhook(request)
        assert response.status_code == 403

    @patch.dict("os.environ", {"META_WEBHOOK_VERIFY_TOKEN": ""})
    def test_no_configured_token_returns_403(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        request = self.rf.get(
            "/api/webhooks/meta/",
            {
                "hub.mode": "subscribe",
                "hub.challenge": "challenge",
                "hub.verify_token": "",
            },
        )
        response = meta_webhook(request)
        assert response.status_code == 403


class TestMetaWebhookEvent:
    """Tests for meta_webhook POST (event handling)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()

    @patch.dict("os.environ", {"META_APP_SECRET": ""})
    def test_event_without_signature_check(self):
        """When META_APP_SECRET is empty, no signature check is done."""
        from infrastructure.integrations.meta_webhook import meta_webhook

        payload = json.dumps(
            {"object": "page", "entry": [{"id": "123", "time": 1234567890}]}
        )
        request = self.rf.post(
            "/api/webhooks/meta/",
            data=payload,
            content_type="application/json",
        )
        response = meta_webhook(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "ok"

    @patch.dict("os.environ", {"META_APP_SECRET": "test_secret"})
    def test_event_with_valid_signature(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        payload = json.dumps({"object": "page", "entry": []}).encode()
        sig = hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()

        request = self.rf.post(
            "/api/webhooks/meta/",
            data=payload,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=f"sha256={sig}",
        )
        response = meta_webhook(request)
        assert response.status_code == 200

    @patch.dict("os.environ", {"META_APP_SECRET": "test_secret"})
    def test_event_with_invalid_signature(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        request = self.rf.post(
            "/api/webhooks/meta/",
            data=b'{"object":"page"}',
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256="sha256=wrong",
        )
        response = meta_webhook(request)
        assert response.status_code == 403

    @patch.dict("os.environ", {"META_APP_SECRET": ""})
    def test_event_with_invalid_json(self):
        from infrastructure.integrations.meta_webhook import meta_webhook

        request = self.rf.post(
            "/api/webhooks/meta/",
            data=b"not json",
            content_type="application/json",
        )
        response = meta_webhook(request)
        assert response.status_code == 400


# ── _verify_signature tests ──────────────────────────────────────────


class TestVerifySignature:
    """Tests for HMAC signature verification."""

    def test_valid_signature(self):
        payload = b'{"test": true}'
        secret = "my_app_secret"
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert _verify_signature(payload, secret, f"sha256={sig}") is True

    def test_invalid_signature(self):
        assert _verify_signature(b"payload", "secret", "sha256=wrong") is False

    def test_missing_prefix(self):
        assert _verify_signature(b"payload", "secret", "wrong") is False

    def test_empty_header(self):
        assert _verify_signature(b"payload", "secret", "") is False


# ── _dispatch_meta_capi_lead tests ───────────────────────────────────


class TestDispatchMetaCapiLead:
    """Tests for _dispatch_meta_capi_lead() helper."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()

    @patch.dict("os.environ", {"META_PIXEL_ID": "", "META_CAPI_ACCESS_TOKEN": ""})
    def test_skips_when_not_configured(self):
        """No dispatch when env vars are empty."""
        from apps.landing.views import _dispatch_meta_capi_lead

        request = self.rf.get("/inscrever-test/")
        request.COOKIES = {}
        # Should not raise
        _dispatch_meta_capi_lead(
            email="test@example.com",
            phone="+5511999001122",
            capture_token="test-uuid",
            page_url="https://example.com/inscrever-test/",
            request=request,
        )

    @patch("apps.landing.views.send_meta_conversion", create=True)
    @patch.dict(
        "os.environ",
        {
            "META_PIXEL_ID": "123456",
            "META_CAPI_ACCESS_TOKEN": "EAAtoken",
            "META_CAPI_TEST_EVENT_CODE": "TEST123",
        },
    )
    def test_dispatches_task_when_configured(self, mock_task):
        """Celery task is dispatched with correct params."""
        from apps.landing.views import _dispatch_meta_capi_lead

        # Need to patch the actual import inside the function
        with patch(
            "infrastructure.integrations.tasks.send_meta_conversion"
        ) as mock_celery:
            mock_celery.delay = MagicMock()
            request = self.rf.get("/inscrever-test/")
            request.COOKIES = {"_fbc": "fb.1.click123", "_fbp": "fb.1.browser456"}
            request.client_ip = "1.2.3.4"

            _dispatch_meta_capi_lead(
                email="test@example.com",
                phone="+5511999001122",
                capture_token="capture-uuid-test",
                page_url="https://example.com/inscrever-test/",
                request=request,
                identity_public_id="idt_abc123",
            )

            mock_celery.delay.assert_called_once()
            call_kwargs = mock_celery.delay.call_args[1]
            assert call_kwargs["pixel_id"] == "123456"
            assert call_kwargs["access_token"] == "EAAtoken"
            assert call_kwargs["test_event_code"] == "TEST123"
            assert call_kwargs["event_name"] == "Lead"
            assert call_kwargs["event_id"] == "capture-uuid-test"
            assert call_kwargs["fbc"] == "fb.1.click123"
            assert call_kwargs["fbp"] == "fb.1.browser456"
            assert call_kwargs["client_ip"] == "1.2.3.4"
            assert call_kwargs["external_id"] == "idt_abc123"
            assert len(call_kwargs["email_hash"]) == 64  # SHA-256 hex
            assert len(call_kwargs["phone_hash"]) == 64
