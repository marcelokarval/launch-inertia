"""Smoke tests for landing admin registration."""

from django.contrib import admin

from apps.landing.models import LeadCaptureIdempotencyKey, LeadIntegrationOutbox


def test_outbox_admin_registered():
    model_admin = admin.site._registry[LeadIntegrationOutbox]

    assert model_admin is not None
    assert "integration_type" in model_admin.list_display
    assert "status" in model_admin.list_display
    assert "attempts" in model_admin.list_display
    assert "capture_submission" in model_admin.readonly_fields


def test_idempotency_admin_registered():
    model_admin = admin.site._registry[LeadCaptureIdempotencyKey]

    assert model_admin is not None
    assert "status" in model_admin.list_display
    assert "request_id" in model_admin.list_display
    assert "email_normalized" in model_admin.list_display
    assert "key" in model_admin.readonly_fields
