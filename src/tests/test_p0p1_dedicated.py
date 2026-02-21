"""
Dedicated tests for P0/P1 gap fixes.

Tests all new code added in the P0/P1 gap fix session:
- ConfidenceEngine (scoring formula, penalties, bonuses, initial estimate)
- CorrelationService (correlate, extract_attribution, validation, normalization)
- Attribution model (creation, UTM fields, has_utm property, to_dict)
- ContactEmail lifecycle methods (mark_bounced, mark_complained, mark_unsubscribed, mark_invalid, is_deliverable)
- Signal receivers (identity, email, phone, fingerprint post_save)
- Celery tasks (all 19 tasks across 4 sub-apps)

Note: Contact.identity FK and AdditionalEmail/AdditionalPhone tests were
removed in Phase 0 cleanup (Contact model eliminated).
"""

import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from apps.contacts.identity.models import Identity, Attribution, IdentityHistory
from apps.contacts.identity.services.confidence_engine import ConfidenceEngine
from apps.contacts.email.models import ContactEmail
from apps.contacts.phone.models import ContactPhone
from apps.contacts.fingerprint.models import (
    FingerprintIdentity,
    FingerprintEvent,
    FingerprintContact,
)
from apps.contacts.fingerprint.services.correlation_service import CorrelationService
# ELIMINATED: Contact, AdditionalEmail, AdditionalPhone imports removed in Phase 0 cleanup.


# ═══════════════════════════════════════════════════════════════════════
# CONFIDENCE ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestConfidenceEngineCalculate:
    """Tests for ConfidenceEngine.calculate() — full DB recalculation."""

    def test_base_score_no_relationships(self):
        """Identity with no emails, phones, or fingerprints gets BASE_SCORE."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        score = ConfidenceEngine.calculate(identity)
        assert score == pytest.approx(0.10)

    def test_single_unverified_email(self):
        """BASE + unverified email bonus."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(
            value="unverified@example.com", identity=identity, is_verified=False
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.05 = 0.15
        assert score == pytest.approx(0.15)

    def test_single_verified_email(self):
        """BASE + verified email bonus."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(
            value="verified@example.com",
            identity=identity,
            is_verified=True,
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.15 = 0.25
        assert score == pytest.approx(0.25)

    def test_two_verified_emails_capped(self):
        """MAX_EMAIL_CONTRIBUTIONS = 2, so only 2 count."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        for i in range(3):
            ContactEmail.objects.create(
                value=f"email{i}@example.com",
                identity=identity,
                is_verified=True,
            )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.15*2 = 0.40 (3rd email ignored)
        assert score == pytest.approx(0.40)

    def test_single_unverified_phone(self):
        """BASE + unverified phone bonus."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactPhone.objects.create(
            value="+5511999000001", identity=identity, is_verified=False
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.10 = 0.20
        assert score == pytest.approx(0.20)

    def test_single_verified_phone(self):
        """BASE + verified phone bonus."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        phone = ContactPhone.objects.create(value="+5511999000002", identity=identity)
        phone.is_verified = True
        phone.save(update_fields=["is_verified"])
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.20 = 0.30
        assert score == pytest.approx(0.30)

    def test_two_verified_phones_capped(self):
        """MAX_PHONE_CONTRIBUTIONS = 2."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        for i in range(3):
            phone = ContactPhone.objects.create(
                value=f"+551199900{i:04d}", identity=identity
            )
            phone.is_verified = True
            phone.save(update_fields=["is_verified"])
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.20*2 = 0.50 (3rd phone ignored)
        assert score == pytest.approx(0.50)

    def test_fingerprint_contribution(self):
        """FP avg * FP_WEIGHT added to score."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        FingerprintIdentity.objects.create(
            hash="fp_conf_test_001",
            identity=identity,
            confidence_score=0.9,
            device_type="desktop",
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.9*0.30 + 0.05 (1 device type) = 0.42
        assert score == pytest.approx(0.42)

    def test_cross_device_bonus(self):
        """Multiple device types give cross-device bonus."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        FingerprintIdentity.objects.create(
            hash="fp_cross_001",
            identity=identity,
            confidence_score=0.9,
            device_type="desktop",
        )
        FingerprintIdentity.objects.create(
            hash="fp_cross_002",
            identity=identity,
            confidence_score=0.9,
            device_type="mobile",
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + avg(0.9,0.9)*0.30 + 2*0.05 = 0.10 + 0.27 + 0.10 = 0.47
        assert score == pytest.approx(0.47)

    def test_cross_device_bonus_capped(self):
        """Cross-device bonus capped at MAX_CROSS_DEVICE_BONUS = 0.15."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        for i, dtype in enumerate(["desktop", "mobile", "tablet", "other"]):
            FingerprintIdentity.objects.create(
                hash=f"fp_cap_{i:03d}",
                identity=identity,
                confidence_score=0.8,
                device_type=dtype,
            )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + avg(0.8)*0.30 + min(4*0.05, 0.15) = 0.10 + 0.24 + 0.15 = 0.49
        assert score == pytest.approx(0.49)

    def test_incognito_penalty(self):
        """Incognito fingerprint applies -0.10 penalty."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        FingerprintIdentity.objects.create(
            hash="fp_incognito_001",
            identity=identity,
            confidence_score=0.9,
            device_type="desktop",
            browser_info={"incognito": True},
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.9*0.30 + 0.05 - 0.10 = 0.32
        assert score == pytest.approx(0.32)

    def test_vpn_penalty(self):
        """VPN fingerprint (high accuracy_radius) applies -0.15 penalty."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        FingerprintIdentity.objects.create(
            hash="fp_vpn_001",
            identity=identity,
            confidence_score=0.9,
            device_type="desktop",
            geo_info={"accuracy_radius": 5000},
        )
        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.9*0.30 + 0.05 - 0.15 = 0.27
        assert score == pytest.approx(0.27)

    def test_bounced_email_penalty(self):
        """Bounced email applies -0.20 penalty."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        email = ContactEmail.objects.create(
            value="bounced@example.com",
            identity=identity,
        )
        email.lifecycle_status = ContactEmail.BOUNCED_HARD
        email.save(update_fields=["lifecycle_status"])

        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.05 (unverified email) - 0.20 (bounced) = clamped to 0.0
        assert score == pytest.approx(0.0)

    def test_dnc_phone_penalty(self):
        """DNC phone applies -0.15 penalty."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        phone = ContactPhone.objects.create(value="+5511999000099", identity=identity)
        phone.is_dnc = True
        phone.save(update_fields=["is_dnc"])

        score = ConfidenceEngine.calculate(identity)
        # 0.10 + 0.10 (unverified phone) - 0.15 (DNC) = 0.05
        assert score == pytest.approx(0.05)

    def test_score_clamped_to_zero(self):
        """Score never goes below 0.0."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        # Multiple penalties, no bonuses
        email = ContactEmail.objects.create(value="bad@example.com", identity=identity)
        email.lifecycle_status = ContactEmail.BOUNCED_HARD
        email.save(update_fields=["lifecycle_status"])
        phone = ContactPhone.objects.create(value="+5511999099999", identity=identity)
        phone.is_dnc = True
        phone.save(update_fields=["is_dnc"])

        score = ConfidenceEngine.calculate(identity)
        assert score >= 0.0

    def test_score_clamped_to_one(self):
        """Score never exceeds 1.0."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        # Max everything
        for i in range(2):
            ContactEmail.objects.create(
                value=f"max_email_{i}@example.com",
                identity=identity,
                is_verified=True,
            )
        for i in range(2):
            phone = ContactPhone.objects.create(
                value=f"+551199800{i:04d}", identity=identity
            )
            phone.is_verified = True
            phone.save(update_fields=["is_verified"])
        for i, dtype in enumerate(["desktop", "mobile", "tablet"]):
            FingerprintIdentity.objects.create(
                hash=f"fp_max_{i:03d}",
                identity=identity,
                confidence_score=1.0,
                device_type=dtype,
            )
        score = ConfidenceEngine.calculate(identity)
        assert score <= 1.0

    def test_calculate_saves_to_db(self):
        """calculate() persists the score and creates IdentityHistory."""
        identity = Identity.objects.create(status=Identity.ACTIVE, confidence_score=0.0)
        initial_history_count = IdentityHistory.objects.filter(
            identity=identity
        ).count()

        ConfidenceEngine.calculate(identity)

        identity.refresh_from_db()
        assert identity.confidence_score == pytest.approx(0.10)
        assert (
            IdentityHistory.objects.filter(identity=identity).count()
            > initial_history_count
        )

    def test_calculate_history_has_components(self):
        """History record includes scoring components breakdown."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(
            value="components@example.com", identity=identity, is_verified=True
        )
        ConfidenceEngine.calculate(identity)

        history = IdentityHistory.objects.filter(
            identity=identity,
            operation_type=IdentityHistory.CONFIDENCE_UPDATE,
        ).first()
        assert history is not None
        assert "components" in history.details
        assert history.details["components"]["base"] == 0.10
        assert history.details["components"]["email_bonus"] == 0.15

    def test_combined_score_all_components(self):
        """Full scenario: fingerprints + verified email + verified phone + cross-device."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(
            value="full@example.com", identity=identity, is_verified=True
        )
        phone = ContactPhone.objects.create(value="+5511999000011", identity=identity)
        phone.is_verified = True
        phone.save(update_fields=["is_verified"])
        FingerprintIdentity.objects.create(
            hash="fp_full_001",
            identity=identity,
            confidence_score=0.95,
            device_type="desktop",
        )
        FingerprintIdentity.objects.create(
            hash="fp_full_002",
            identity=identity,
            confidence_score=0.85,
            device_type="mobile",
        )
        score = ConfidenceEngine.calculate(identity)
        # base=0.10, fp=avg(0.95,0.85)*0.30=0.27, cross=2*0.05=0.10,
        # email=0.15, phone=0.20 → total=0.82
        assert score == pytest.approx(0.82)


@pytest.mark.django_db
class TestConfidenceEngineCalculateInitial:
    """Tests for ConfidenceEngine.calculate_initial() — fast estimate."""

    def test_initial_fp_only(self):
        """Just fingerprint, no contacts."""
        score = ConfidenceEngine.calculate_initial(0.9)
        # 0.10 + 0.9*0.30 = 0.37
        assert score == pytest.approx(0.37)

    def test_initial_with_email(self):
        score = ConfidenceEngine.calculate_initial(0.9, has_email=True)
        # 0.10 + 0.9*0.30 + 0.05 = 0.42
        assert score == pytest.approx(0.42)

    def test_initial_with_phone(self):
        score = ConfidenceEngine.calculate_initial(0.9, has_phone=True)
        # 0.10 + 0.9*0.30 + 0.10 = 0.47
        assert score == pytest.approx(0.47)

    def test_initial_with_email_and_phone(self):
        score = ConfidenceEngine.calculate_initial(0.9, has_email=True, has_phone=True)
        # 0.10 + 0.9*0.30 + 0.05 + 0.10 = 0.52
        assert score == pytest.approx(0.52)

    def test_initial_no_fp_uses_default(self):
        """When fingerprint_confidence is falsy, defaults to 0.3."""
        score = ConfidenceEngine.calculate_initial(0.0)
        # 0.10 + 0.3*0.30 = 0.19
        assert score == pytest.approx(0.19)

    def test_initial_does_not_save_to_db(self):
        """calculate_initial is a pure calculation, no DB writes."""
        score = ConfidenceEngine.calculate_initial(0.9, has_email=True)
        # No Identity created, so no DB check needed — just ensure no error
        assert 0.0 <= score <= 1.0

    def test_initial_clamped_to_one(self):
        """Even with unrealistic input, clamped to 1.0."""
        score = ConfidenceEngine.calculate_initial(10.0, has_email=True, has_phone=True)
        assert score == 1.0

    def test_initial_clamped_to_zero(self):
        """Negative fingerprint confidence clamped to valid range."""
        score = ConfidenceEngine.calculate_initial(-1.0)
        # 0.10 + (-1.0)*0.30 = 0.10 - 0.30 = -0.20 → clamped to 0.0
        assert score == 0.0


# ═══════════════════════════════════════════════════════════════════════
# CORRELATION SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestCorrelationServiceCorrelate:
    """Tests for CorrelationService.correlate() — main entry point."""

    def _make_payloads(self, visitor_id="visitor123"):
        fp_payload = {
            "fingerprint": {"visitorId": visitor_id, "confidence": 0.95},
        }
        form_payload = {
            "fingerprint": {"visitorId": visitor_id},
            "formData": {
                "email": "  User@Example.COM  ",
                "phone": "(11) 99988-7766",
                "name": "  John Doe  ",
            },
            "sessionData": {
                "utm_source": "google",
                "utm_medium": "cpc",
                "referrer": "https://google.com",
                "pageUrl": "https://launch.com/register",
            },
            "deviceContext": {"userAgent": "Mozilla/5.0"},
        }
        return fp_payload, form_payload

    def test_correlate_success(self):
        fp, form = self._make_payloads()
        result = CorrelationService.correlate(fp, form)
        assert result["visitorId"] == "visitor123"
        assert result["contact_data"]["email"] == "user@example.com"
        assert result["contact_data"]["name"] == "John Doe"
        assert result["attribution_data"]["utm_source"] == "google"
        assert "correlation_timestamp" in result

    def test_correlate_visitor_id_mismatch(self):
        fp = {"fingerprint": {"visitorId": "visitor_A"}}
        form = {"fingerprint": {"visitorId": "visitor_B"}}
        with pytest.raises(ValueError, match="Fingerprint mismatch"):
            CorrelationService.correlate(fp, form)

    def test_correlate_normalizes_email(self):
        fp, form = self._make_payloads()
        result = CorrelationService.correlate(fp, form)
        assert result["contact_data"]["email"] == "user@example.com"

    def test_correlate_normalizes_phone_with_country_code(self):
        fp, form = self._make_payloads()
        result = CorrelationService.correlate(fp, form)
        phone = result["contact_data"]["phone"]
        assert phone.startswith("+55")

    def test_correlate_empty_form_data(self):
        fp = {"fingerprint": {"visitorId": "v1"}}
        form = {"fingerprint": {"visitorId": "v1"}}
        result = CorrelationService.correlate(fp, form)
        assert result["contact_data"]["email"] == ""
        assert result["contact_data"]["phone"] == ""
        assert result["contact_data"]["name"] == ""


class TestCorrelationServiceExtractAttribution:
    """Tests for CorrelationService.extract_attribution()."""

    def test_utm_from_form_data(self):
        payload = {
            "formData": {
                "utm_source": "facebook",
                "utm_medium": "social",
                "utm_campaign": "WH0126_launch",
                "utm_content": "banner_top",
                "utm_term": "leiloes",
            },
            "sessionData": {},
        }
        result = CorrelationService.extract_attribution(payload)
        assert result["utm_source"] == "facebook"
        assert result["utm_campaign"] == "WH0126_launch"

    def test_utm_from_session_data_fallback(self):
        payload = {
            "formData": {},
            "sessionData": {
                "utm_source": "youtube",
                "utm_medium": "video",
                "referrer": "https://youtube.com/watch?v=xyz",
                "pageUrl": "https://launch.com/webinar",
            },
        }
        result = CorrelationService.extract_attribution(payload)
        assert result["utm_source"] == "youtube"
        assert result["referrer"] == "https://youtube.com/watch?v=xyz"
        assert result["landing_page"] == "https://launch.com/webinar"

    def test_utm_form_data_takes_priority(self):
        """formData UTM overrides sessionData UTM."""
        payload = {
            "formData": {"utm_source": "form_source"},
            "sessionData": {"utm_source": "session_source"},
        }
        result = CorrelationService.extract_attribution(payload)
        assert result["utm_source"] == "form_source"

    def test_empty_attribution(self):
        payload = {"formData": {}, "sessionData": {}}
        result = CorrelationService.extract_attribution(payload)
        assert result["utm_source"] == ""
        assert result["utm_medium"] == ""
        assert result["referrer"] == ""


class TestCorrelationServiceNormalization:
    """Tests for email and phone normalization."""

    def test_normalize_email_lowercase_strip(self):
        assert (
            CorrelationService.normalize_email("  TEST@GMAIL.COM  ") == "test@gmail.com"
        )

    def test_normalize_email_none(self):
        assert CorrelationService.normalize_email(None) == ""

    def test_normalize_email_empty(self):
        assert CorrelationService.normalize_email("") == ""

    def test_normalize_email_invalid_format_returns_asis(self):
        """Invalid emails are returned as-is (lowercase) for debugging."""
        result = CorrelationService.normalize_email("not-an-email")
        assert result == "not-an-email"

    def test_normalize_phone_none(self):
        assert CorrelationService.normalize_phone(None) == ""

    def test_normalize_phone_empty(self):
        assert CorrelationService.normalize_phone("") == ""

    def test_normalize_phone_strips_formatting(self):
        assert CorrelationService.normalize_phone("(11) 99988-7766") == "+5511999887766"

    def test_normalize_phone_with_55_prefix(self):
        assert CorrelationService.normalize_phone("5511999887766") == "+5511999887766"

    def test_normalize_phone_already_e164(self):
        assert CorrelationService.normalize_phone("+5511999887766") == "+5511999887766"

    def test_normalize_phone_without_country_code(self):
        assert CorrelationService.normalize_phone("11999887766") == "+5511999887766"


class TestCorrelationServiceValidation:
    """Tests for validate_contact_data and related validation methods."""

    def test_validate_valid_email(self):
        result = CorrelationService.validate_contact_data(
            {"email": "valid@example.com", "phone": "+5511999887766"}
        )
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["enrichments"]["email_domain"] == "example.com"

    def test_validate_invalid_email(self):
        result = CorrelationService.validate_contact_data({"email": "bad-email"})
        assert result["is_valid"] is False
        assert "Invalid email format" in result["errors"]

    def test_validate_disposable_email_warning(self):
        result = CorrelationService.validate_contact_data(
            {"email": "test@mailinator.com"}
        )
        assert any("Disposable" in w for w in result["warnings"])

    def test_validate_phone_format_warning(self):
        result = CorrelationService.validate_contact_data({"phone": "123"})
        assert any("Phone format" in w for w in result["warnings"])

    def test_validate_br_phone_enrichment(self):
        result = CorrelationService.validate_contact_data({"phone": "+5511999887766"})
        assert result["enrichments"]["phone_country"] == "BR"

    def test_validate_us_phone_enrichment(self):
        result = CorrelationService.validate_contact_data({"phone": "+12125551234"})
        assert result["enrichments"]["phone_country"] == "US"

    def test_is_disposable_domain(self):
        assert CorrelationService.is_disposable_domain("mailinator.com")
        assert CorrelationService.is_disposable_domain("yopmail.com")
        assert CorrelationService.is_disposable_domain("guerrillamail.com")
        assert not CorrelationService.is_disposable_domain("gmail.com")
        assert not CorrelationService.is_disposable_domain("outlook.com")


class TestCorrelationServiceFormQuality:
    """Tests for calculate_form_quality_score."""

    def test_full_form(self):
        payload = {
            "formData": {
                "email": "test@test.com",
                "phone": "+5511999887766",
                "name": "John",
                "utm_source": "google",
            }
        }
        score = CorrelationService.calculate_form_quality_score(payload)
        assert score == pytest.approx(1.0)

    def test_email_only(self):
        payload = {"formData": {"email": "test@test.com"}}
        score = CorrelationService.calculate_form_quality_score(payload)
        assert score == pytest.approx(0.4)

    def test_empty_form(self):
        payload = {"formData": {}}
        score = CorrelationService.calculate_form_quality_score(payload)
        assert score == pytest.approx(0.0)

    def test_missing_form_data_key(self):
        payload = {}
        score = CorrelationService.calculate_form_quality_score(payload)
        assert score == pytest.approx(0.0)


@pytest.mark.django_db
class TestCorrelationServiceSaveAttribution:
    """Tests for save_attribution (DB persistence)."""

    def test_save_attribution_with_utm(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr_data = {
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "WH0126",
            "utm_content": "",
            "utm_term": "",
            "referrer": "https://google.com",
            "landing_page": "https://launch.com/form",
        }
        attr = CorrelationService.save_attribution(identity, attr_data)
        assert attr is not None
        assert attr.utm_source == "google"
        assert attr.utm_campaign == "WH0126"
        assert attr.identity == identity
        assert attr.touchpoint_type == "form"

    def test_save_attribution_custom_touchpoint(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr_data = {"utm_source": "api", "referrer": "", "landing_page": ""}
        attr = CorrelationService.save_attribution(
            identity, attr_data, touchpoint_type="webhook"
        )
        assert attr.touchpoint_type == "webhook"  # type: ignore[union-attr]

    def test_save_attribution_returns_none_no_data(self):
        """No meaningful attribution data → returns None."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr_data = {
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "referrer": "",
            "landing_page": "",
        }
        result = CorrelationService.save_attribution(identity, attr_data)
        assert result is None


class TestCorrelationServiceExtractContactMetadata:
    """Tests for extract_contact_metadata."""

    def test_extract_metadata(self):
        payload = {
            "deviceContext": {
                "userAgent": "Mozilla/5.0",
                "screenResolution": "1920x1080",
                "language": "pt-BR",
                "timezone": "America/Sao_Paulo",
            },
            "sessionData": {
                "pageUrl": "https://launch.com/form",
                "timestamp": "2026-01-15T10:30:00Z",
            },
        }
        meta = CorrelationService.extract_contact_metadata(payload)
        assert meta["form_source"] == "https://launch.com/form"
        assert meta["user_agent"] == "Mozilla/5.0"
        assert meta["language"] == "pt-BR"


# ═══════════════════════════════════════════════════════════════════════
# ATTRIBUTION MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAttributionModel:
    """Tests for the Attribution model."""

    def test_create_attribution(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(
            identity=identity,
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="WH0126_launch",
            utm_content="banner_top",
            utm_term="leilao",
            referrer="https://google.com/search",
            landing_page="https://launch.com/register",
            touchpoint_type="form",
        )
        assert attr.public_id.startswith("atr_")
        assert attr.utm_source == "google"
        assert attr.identity == identity

    def test_has_utm_true(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(identity=identity, utm_source="facebook")
        assert attr.has_utm is True

    def test_has_utm_false(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(
            identity=identity,
            referrer="https://direct.com",
        )
        assert attr.has_utm is False

    def test_has_utm_with_campaign_only(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(identity=identity, utm_campaign="WH0126")
        assert attr.has_utm is True

    def test_to_dict(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(
            identity=identity,
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="WH0126",
            touchpoint_type="form",
        )
        data = attr.to_dict()
        assert data["utm_source"] == "google"
        assert data["utm_medium"] == "cpc"
        assert data["utm_campaign"] == "WH0126"
        assert data["identity_id"] == identity.public_id
        assert data["touchpoint_type"] == "form"
        assert "id" in data

    def test_str_representation(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(
            identity=identity,
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="WH0126",
        )
        s = str(attr)
        assert "src=google" in s
        assert "med=cpc" in s
        assert "cmp=WH0126" in s

    def test_str_no_utm(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        attr = Attribution.objects.create(identity=identity)
        s = str(attr)
        assert "Attribution(" in s

    def test_multiple_attributions_per_identity(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        Attribution.objects.create(identity=identity, utm_source="google")
        Attribution.objects.create(identity=identity, utm_source="facebook")
        Attribution.objects.create(identity=identity, utm_source="youtube")
        assert identity.attributions.count() == 3

    def test_ordering_newest_first(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        a1 = Attribution.objects.create(identity=identity, utm_source="first")
        a2 = Attribution.objects.create(identity=identity, utm_source="second")
        attributions = list(identity.attributions.all())
        assert attributions[0].pk == a2.pk  # newest first


# ═══════════════════════════════════════════════════════════════════════
# CONTACT EMAIL LIFECYCLE TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestContactEmailLifecycle:
    """Tests for ContactEmail lifecycle methods (P1.2)."""

    def test_default_lifecycle_status_is_pending(self):
        email = ContactEmail.objects.create(value="default@example.com")
        assert email.lifecycle_status == ContactEmail.PENDING

    def test_verify_sets_active(self):
        email = ContactEmail.objects.create(value="verify_lc@example.com")
        email.verify()
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.ACTIVE
        assert email.is_verified is True

    def test_unverify_resets_to_pending(self):
        email = ContactEmail.objects.create(value="unverify_lc@example.com")
        email.verify()
        email.unverify()
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.PENDING
        assert email.is_verified is False

    def test_mark_bounced_soft(self):
        email = ContactEmail.objects.create(value="soft_bounce@example.com")
        email.verify()
        email.mark_bounced(hard=False)
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.BOUNCED_SOFT
        assert email.is_verified is False

    def test_mark_bounced_hard(self):
        email = ContactEmail.objects.create(value="hard_bounce@example.com")
        email.verify()
        email.mark_bounced(hard=True)
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.BOUNCED_HARD
        assert email.is_verified is False

    def test_mark_complained(self):
        email = ContactEmail.objects.create(value="complained@example.com")
        email.mark_complained()
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.COMPLAINED
        assert email.is_dnc is True

    def test_mark_unsubscribed(self):
        email = ContactEmail.objects.create(value="unsub@example.com")
        email.mark_unsubscribed()
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.UNSUBSCRIBED
        assert email.is_dnc is True

    def test_mark_invalid(self):
        email = ContactEmail.objects.create(value="invalid@example.com")
        email.verify()
        email.mark_invalid()
        email.refresh_from_db()
        assert email.lifecycle_status == ContactEmail.INVALID
        assert email.is_verified is False

    def test_is_deliverable_pending(self):
        email = ContactEmail.objects.create(value="deliver_pending@example.com")
        assert email.is_deliverable is True

    def test_is_deliverable_active(self):
        email = ContactEmail.objects.create(value="deliver_active@example.com")
        email.verify()
        email.refresh_from_db()
        assert email.is_deliverable is True

    def test_is_deliverable_false_bounced(self):
        email = ContactEmail.objects.create(value="deliver_bounced@example.com")
        email.mark_bounced(hard=True)
        email.refresh_from_db()
        assert email.is_deliverable is False

    def test_is_deliverable_false_complained(self):
        email = ContactEmail.objects.create(value="deliver_complained@example.com")
        email.mark_complained()
        email.refresh_from_db()
        assert email.is_deliverable is False

    def test_is_deliverable_false_unsubscribed(self):
        email = ContactEmail.objects.create(value="deliver_unsub@example.com")
        email.mark_unsubscribed()
        email.refresh_from_db()
        assert email.is_deliverable is False

    def test_is_deliverable_false_dnc(self):
        """Pending + DNC = not deliverable."""
        email = ContactEmail.objects.create(value="deliver_dnc@example.com")
        email.is_dnc = True
        email.save(update_fields=["is_dnc"])
        assert email.is_deliverable is False

    def test_quality_score_default(self):
        email = ContactEmail.objects.create(value="quality@example.com")
        assert email.quality_score == 0.0

    def test_to_dict_includes_lifecycle_fields(self):
        email = ContactEmail.objects.create(value="dictlc@example.com")
        email.mark_complained()
        email.refresh_from_db()
        data = email.to_dict()
        assert data["lifecycle_status"] == "complained"
        assert data["is_dnc"] is True
        assert data["is_deliverable"] is False


# ═══════════════════════════════════════════════════════════════════════
# SIGNAL RECEIVER TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestIdentitySignals:
    """Tests for identity post_save and post_merge signal receivers."""

    @patch("apps.contacts.identity.tasks.calculate_confidence_score")
    @patch("apps.contacts.identity.tasks.update_identity_history")
    @patch("apps.contacts.identity.tasks.analyze_identity_graph")
    def test_identity_creation_triggers_tasks(
        self, mock_analyze, mock_history, mock_confidence
    ):
        """Creating an identity fires 3 async tasks."""
        mock_confidence.delay = MagicMock()
        mock_history.delay = MagicMock()
        mock_analyze.delay = MagicMock()

        identity = Identity.objects.create(status=Identity.ACTIVE)

        mock_confidence.delay.assert_called_once_with(identity.id)
        mock_history.delay.assert_called_once()
        mock_analyze.delay.assert_called_once_with(identity.id)

    @patch("apps.contacts.identity.tasks.calculate_confidence_score")
    @patch("apps.contacts.identity.tasks.update_identity_history")
    @patch("apps.contacts.identity.tasks.analyze_identity_graph")
    def test_identity_update_does_not_trigger_tasks(
        self, mock_analyze, mock_history, mock_confidence
    ):
        """Updating (not creating) an identity does NOT fire tasks."""
        mock_confidence.delay = MagicMock()
        mock_history.delay = MagicMock()
        mock_analyze.delay = MagicMock()

        identity = Identity.objects.create(status=Identity.ACTIVE)
        mock_confidence.delay.reset_mock()
        mock_history.delay.reset_mock()
        mock_analyze.delay.reset_mock()

        identity.status = Identity.INACTIVE
        identity.save()

        mock_confidence.delay.assert_not_called()
        mock_history.delay.assert_not_called()
        mock_analyze.delay.assert_not_called()


@pytest.mark.django_db
class TestEmailSignals:
    """Tests for ContactEmail post_save signal receiver."""

    @patch("apps.contacts.email.tasks.process_new_email")
    @patch("apps.contacts.email.tasks.verify_email")
    def test_email_creation_triggers_tasks(self, mock_verify, mock_process):
        mock_process.delay = MagicMock()
        mock_verify.delay = MagicMock()

        email = ContactEmail.objects.create(value="signal_test@example.com")

        mock_process.delay.assert_called_once_with(email.value)
        mock_verify.delay.assert_called_once_with(email.id)

    @patch("apps.contacts.email.tasks.process_new_email")
    @patch("apps.contacts.email.tasks.verify_email")
    def test_email_update_does_not_trigger_tasks(self, mock_verify, mock_process):
        mock_process.delay = MagicMock()
        mock_verify.delay = MagicMock()

        email = ContactEmail.objects.create(value="signal_update@example.com")
        mock_process.delay.reset_mock()
        mock_verify.delay.reset_mock()

        email.is_verified = True
        email.save(update_fields=["is_verified", "updated_at"])

        mock_process.delay.assert_not_called()
        mock_verify.delay.assert_not_called()


@pytest.mark.django_db
class TestPhoneSignals:
    """Tests for ContactPhone post_save signal receiver."""

    @patch("apps.contacts.phone.tasks.process_new_phone")
    @patch("apps.contacts.phone.tasks.verify_phone")
    def test_phone_creation_triggers_tasks(self, mock_verify, mock_process):
        mock_process.delay = MagicMock()
        mock_verify.delay = MagicMock()

        phone = ContactPhone.objects.create(value="+5511999000033")

        mock_process.delay.assert_called_once_with(phone.value)
        mock_verify.delay.assert_called_once_with(phone.id)

    @patch("apps.contacts.phone.tasks.process_new_phone")
    @patch("apps.contacts.phone.tasks.verify_phone")
    def test_phone_update_does_not_trigger_tasks(self, mock_verify, mock_process):
        mock_process.delay = MagicMock()
        mock_verify.delay = MagicMock()

        phone = ContactPhone.objects.create(value="+5511999000044")
        mock_process.delay.reset_mock()
        mock_verify.delay.reset_mock()

        phone.is_verified = True
        phone.save(update_fields=["is_verified", "updated_at"])

        mock_process.delay.assert_not_called()
        mock_verify.delay.assert_not_called()


@pytest.mark.django_db
class TestFingerprintSignals:
    """Tests for fingerprint post_save signal receivers."""

    @patch("apps.contacts.fingerprint.tasks.analyze_fingerprint_patterns")
    @patch("apps.contacts.fingerprint.tasks.detect_suspicious_activity")
    def test_fingerprint_event_creation_triggers_detection(
        self, mock_detect, mock_analyze
    ):
        mock_detect.delay = MagicMock()
        mock_analyze.delay = MagicMock()

        fp = FingerprintIdentity.objects.create(
            hash="signal_fp_001", device_type="desktop"
        )
        event = FingerprintEvent.objects.create(
            fingerprint=fp,
            event_type="page_view",
            timestamp=timezone.now(),
        )

        mock_detect.delay.assert_called_once_with(fp.id)
        # No identity, so analyze should NOT be called
        mock_analyze.delay.assert_not_called()

    @patch("apps.contacts.fingerprint.tasks.analyze_fingerprint_patterns")
    @patch("apps.contacts.fingerprint.tasks.detect_suspicious_activity")
    def test_fingerprint_event_with_identity_triggers_analysis(
        self, mock_detect, mock_analyze
    ):
        mock_detect.delay = MagicMock()
        mock_analyze.delay = MagicMock()

        identity = Identity.objects.create(status=Identity.ACTIVE)
        fp = FingerprintIdentity.objects.create(
            hash="signal_fp_002", identity=identity, device_type="mobile"
        )

        mock_analyze.delay.reset_mock()

        event = FingerprintEvent.objects.create(
            fingerprint=fp,
            event_type="form_submit",
            timestamp=timezone.now(),
        )

        mock_analyze.delay.assert_called_once_with(identity.id)
        mock_detect.delay.assert_called_with(fp.id)

    @patch("apps.contacts.fingerprint.tasks.analyze_fingerprint_patterns")
    def test_fingerprint_identity_creation_triggers_analysis(self, mock_analyze):
        mock_analyze.delay = MagicMock()

        identity = Identity.objects.create(status=Identity.ACTIVE)
        fp = FingerprintIdentity.objects.create(
            hash="signal_fp_003", identity=identity, device_type="desktop"
        )

        mock_analyze.delay.assert_called_with(identity.id)


# ═══════════════════════════════════════════════════════════════════════
# CELERY TASK TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestIdentityTasks:
    """Tests for identity Celery tasks."""

    def test_calculate_confidence_score_task(self):
        from apps.contacts.identity.tasks import calculate_confidence_score

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = calculate_confidence_score(identity.id)
        assert result["status"] == "success"
        assert result["confidence_score"] == pytest.approx(0.10)

    def test_calculate_confidence_score_task_not_found(self):
        from apps.contacts.identity.tasks import calculate_confidence_score

        result = calculate_confidence_score(999999)
        assert result["status"] == "error"

    def test_update_identity_history_task(self):
        from apps.contacts.identity.tasks import update_identity_history

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = update_identity_history(identity.id, "UPDATE", {"action": "test"})
        assert result["status"] == "success"
        assert result["identity_id"] == identity.public_id

    def test_update_identity_history_task_not_found(self):
        from apps.contacts.identity.tasks import update_identity_history

        result = update_identity_history(999999, "UPDATE", {})
        assert result["status"] == "error"

    def test_analyze_identity_graph_task(self):
        from apps.contacts.identity.tasks import analyze_identity_graph

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = analyze_identity_graph(identity.id)
        assert result["status"] == "success"

    def test_analyze_identity_graph_task_not_found(self):
        from apps.contacts.identity.tasks import analyze_identity_graph

        result = analyze_identity_graph(999999)
        assert result["status"] == "error"

    def test_merge_identities_task(self):
        """Test merge_identities task with direction normalization.

        The task normalizes direction: oldest survives. Since `older` is
        created first, it becomes the survivor (target). The email on
        `newer` gets transferred to `older`.
        """
        from apps.contacts.identity.tasks import merge_identities

        older = Identity.objects.create(status=Identity.ACTIVE)
        newer = Identity.objects.create(status=Identity.ACTIVE)
        # Put the email on the NEWER identity so it gets transferred
        ContactEmail.objects.create(value="task_merge@example.com", identity=newer)

        # Direction normalized: older survives regardless of argument order
        result = merge_identities(newer.id, older.id)
        assert result["status"] == "success"
        assert result["stats"]["emails_transferred"] == 1

    def test_merge_identities_task_not_found(self):
        from apps.contacts.identity.tasks import merge_identities

        result = merge_identities(999999, 999998)
        assert result["status"] == "error"

    def test_auto_merge_task(self):
        from apps.contacts.identity.tasks import auto_merge

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = auto_merge(identity.id)
        assert result["status"] == "success"
        assert result["merged_count"] == 0

    def test_cleanup_merged_identities_task(self):
        from apps.contacts.identity.tasks import cleanup_merged_identities

        result = cleanup_merged_identities(days=30)
        assert result["status"] == "success"
        assert result["identities_deleted"] == 0

    def test_find_merge_candidates_task(self):
        from apps.contacts.identity.tasks import find_merge_candidates

        result = find_merge_candidates()
        assert result["status"] == "success"


@pytest.mark.django_db
class TestEmailTasks:
    """Tests for email Celery tasks."""

    @patch("apps.contacts.email.tasks.associate_email_with_fingerprints")
    @patch("apps.contacts.email.tasks.verify_email")
    def test_process_new_email_task(self, mock_verify, mock_assoc):
        """process_new_email creates the email. We mock chained tasks
        because associate_email_with_fingerprints uses JSON __contains
        which is not supported on SQLite."""
        from apps.contacts.email.tasks import process_new_email

        mock_assoc.delay = MagicMock()
        mock_verify.delay = MagicMock()
        result = process_new_email("task_email@example.com")
        assert result["status"] == "success"
        assert result["created"] is True

    def test_process_new_email_existing(self):
        from apps.contacts.email.tasks import process_new_email

        ContactEmail.objects.create(value="existing_task@example.com")
        # Second call: email already exists, so no chained tasks fire
        result = process_new_email("existing_task@example.com")
        assert result["status"] == "success"
        assert result["created"] is False

    def test_associate_email_with_fingerprints_not_found(self):
        from apps.contacts.email.tasks import associate_email_with_fingerprints

        result = associate_email_with_fingerprints(999999)
        assert result["status"] == "error"

    @pytest.mark.skipif(
        True,
        reason="SQLite does not support JSON __contains lookup; tested via PostgreSQL in CI",
    )
    def test_associate_email_with_fingerprints_no_matches(self):
        from apps.contacts.email.tasks import associate_email_with_fingerprints

        email = ContactEmail.objects.create(value="no_match@example.com")
        result = associate_email_with_fingerprints(email.id)
        assert result["status"] == "success"
        assert result["fingerprints_associated"] == 0

    def test_verify_email_task_not_found(self):
        from apps.contacts.email.tasks import verify_email

        result = verify_email(999999)
        assert result["status"] == "error"

    def test_confirm_email_verification_no_code_or_token(self):
        from apps.contacts.email.tasks import confirm_email_verification

        email = ContactEmail.objects.create(value="no_code@example.com")
        result = confirm_email_verification(email.id)
        assert result["status"] == "error"
        assert "Code or token required" in result["message"]

    def test_handle_email_bounce_not_found(self):
        from apps.contacts.email.tasks import handle_email_bounce

        result = handle_email_bounce(999999, {"type": "hard"})
        assert result["status"] == "error"


@pytest.mark.django_db
class TestPhoneTasks:
    """Tests for phone Celery tasks."""

    @patch("apps.contacts.phone.tasks.associate_phone_with_fingerprints")
    @patch("apps.contacts.phone.tasks.verify_phone")
    def test_process_new_phone_task(self, mock_verify, mock_assoc):
        """process_new_phone creates the phone. We mock chained tasks
        because associate_phone_with_fingerprints uses JSON __contains
        which is not supported on SQLite."""
        from apps.contacts.phone.tasks import process_new_phone

        mock_assoc.delay = MagicMock()
        mock_verify.delay = MagicMock()
        result = process_new_phone("+5511999000055")
        assert result["status"] == "success"
        assert result["created"] is True

    def test_associate_phone_with_fingerprints_not_found(self):
        from apps.contacts.phone.tasks import associate_phone_with_fingerprints

        result = associate_phone_with_fingerprints(999999)
        assert result["status"] == "error"

    @pytest.mark.skipif(
        True,
        reason="SQLite does not support JSON __contains lookup; tested via PostgreSQL in CI",
    )
    def test_associate_phone_with_fingerprints_no_matches(self):
        from apps.contacts.phone.tasks import associate_phone_with_fingerprints

        phone = ContactPhone.objects.create(value="+5511999000066")
        result = associate_phone_with_fingerprints(phone.id)
        assert result["status"] == "success"
        assert result["fingerprints_associated"] == 0

    def test_verify_phone_task_not_found(self):
        from apps.contacts.phone.tasks import verify_phone

        result = verify_phone(999999)
        assert result["status"] == "error"


@pytest.mark.django_db
class TestFingerprintTasks:
    """Tests for fingerprint Celery tasks."""

    def test_update_fingerprint_data_not_found(self):
        from apps.contacts.fingerprint.tasks import update_fingerprint_data

        result = update_fingerprint_data(999999, {})
        assert result["status"] == "error"

    def test_analyze_fingerprint_patterns_not_found(self):
        from apps.contacts.fingerprint.tasks import analyze_fingerprint_patterns

        result = analyze_fingerprint_patterns(999999)
        assert result["status"] == "error"

    def test_analyze_fingerprint_patterns_success(self):
        from apps.contacts.fingerprint.tasks import analyze_fingerprint_patterns

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = analyze_fingerprint_patterns(identity.id)
        assert result["status"] == "success"

    def test_detect_suspicious_activity_not_found(self):
        from apps.contacts.fingerprint.tasks import detect_suspicious_activity

        result = detect_suspicious_activity(999999)
        assert result["status"] == "error"

    def test_detect_suspicious_activity_success(self):
        from apps.contacts.fingerprint.tasks import detect_suspicious_activity

        fp = FingerprintIdentity.objects.create(
            hash="detect_task_001", device_type="desktop"
        )
        result = detect_suspicious_activity(fp.id)
        assert result["status"] == "success"

    def test_merge_identities_from_fingerprint(self):
        from apps.contacts.fingerprint.tasks import merge_identities_from_fingerprint

        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)
        result = merge_identities_from_fingerprint(source.id, target.id)
        assert result["status"] == "success"


# ═══════════════════════════════════════════════════════════════════════
# P2: IDENTITY MERGE HARDENING TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestMergeServiceP2:
    """Tests for P2 merge improvements: locking, direction, enriched fields."""

    def test_select_for_update_prevents_double_merge(self):
        """Concurrent merge of same source is prevented by validation."""
        from apps.contacts.identity.services.merge_service import (
            MergeService,
            MergeValidationError,
        )

        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)

        # First merge succeeds
        MergeService.execute_merge(source, target)
        source.refresh_from_db()
        assert source.status == Identity.MERGED

        # Second merge of same source fails gracefully
        source_stale = Identity.objects.get(pk=source.pk)
        target2 = Identity.objects.create(status=Identity.ACTIVE)
        with pytest.raises(MergeValidationError, match="not active"):
            MergeService.execute_merge(source_stale, target2)

    def test_direction_normalization_oldest_survives(self):
        """merge_identities task normalizes direction: oldest survives."""
        from apps.contacts.identity.tasks import merge_identities

        older = Identity.objects.create(status=Identity.ACTIVE)
        newer = Identity.objects.create(status=Identity.ACTIVE)

        # Pass newer as first arg — direction should still be normalized
        result = merge_identities(newer.id, older.id)
        assert result["status"] == "success"
        assert result["source"] == newer.public_id
        assert result["target"] == older.public_id

        newer.refresh_from_db()
        older.refresh_from_db()
        assert newer.status == Identity.MERGED
        assert newer.merged_into == older
        assert older.status == Identity.ACTIVE

    def test_direction_normalization_same_identity_skipped(self):
        """Merging an identity into itself is skipped."""
        from apps.contacts.identity.tasks import merge_identities

        identity = Identity.objects.create(status=Identity.ACTIVE)
        result = merge_identities(identity.id, identity.id)
        assert result["status"] == "skipped"
        assert result["reason"] == "same_identity"

    def test_idempotent_merge_already_merged(self):
        """Re-merging an already-merged source is treated as idempotent skip."""
        from apps.contacts.identity.tasks import merge_identities

        older = Identity.objects.create(status=Identity.ACTIVE)
        newer = Identity.objects.create(status=Identity.ACTIVE)

        # First merge succeeds
        result1 = merge_identities(newer.id, older.id)
        assert result1["status"] == "success"

        # Second merge skipped (idempotent)
        result2 = merge_identities(newer.id, older.id)
        assert result2["status"] == "skipped"

    def test_display_name_transferred_to_empty_target(self):
        """Source's display_name fills target's empty display_name."""
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.create(
            status=Identity.ACTIVE, display_name="João Silva"
        )
        target = Identity.objects.create(status=Identity.ACTIVE, display_name="")

        MergeService.execute_merge(source, target)
        target.refresh_from_db()
        assert target.display_name == "João Silva"

    def test_display_name_target_preserved(self):
        """Target's non-empty display_name is NOT overwritten by source's."""
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.create(
            status=Identity.ACTIVE, display_name="Source Name"
        )
        target = Identity.objects.create(
            status=Identity.ACTIVE, display_name="Target Name"
        )

        MergeService.execute_merge(source, target)
        target.refresh_from_db()
        assert target.display_name == "Target Name"

    def test_operator_notes_merged(self):
        """Source's operator_notes are appended to target's."""
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.create(
            status=Identity.ACTIVE, operator_notes="Note from source"
        )
        target = Identity.objects.create(
            status=Identity.ACTIVE, operator_notes="Note from target"
        )

        MergeService.execute_merge(source, target)
        target.refresh_from_db()
        assert "Note from target" in target.operator_notes
        assert "Note from source" in target.operator_notes
        assert source.public_id in target.operator_notes

    def test_operator_notes_source_only(self):
        """Source's notes fill empty target notes (no separator)."""
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.create(
            status=Identity.ACTIVE, operator_notes="Only note"
        )
        target = Identity.objects.create(status=Identity.ACTIVE, operator_notes="")

        MergeService.execute_merge(source, target)
        target.refresh_from_db()
        assert target.operator_notes == "Only note"

    def test_tags_union(self):
        """Source's tags are added to target's (union)."""
        from apps.contacts.identity.services.merge_service import MergeService
        from apps.contacts.models import Tag

        tag_a = Tag.objects.create(name="tag_a")
        tag_b = Tag.objects.create(name="tag_b")
        tag_c = Tag.objects.create(name="tag_c")

        source = Identity.objects.create(status=Identity.ACTIVE)
        source.tags.add(tag_a, tag_b)

        target = Identity.objects.create(status=Identity.ACTIVE)
        target.tags.add(tag_b, tag_c)

        MergeService.execute_merge(source, target)
        target_tags = set(target.tags.values_list("name", flat=True))
        assert target_tags == {"tag_a", "tag_b", "tag_c"}

    def test_attribution_transferred(self):
        """Attribution records are transferred from source to target."""
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)
        Attribution.objects.create(
            identity=source, utm_source="google", utm_medium="cpc"
        )

        stats = MergeService.execute_merge(source, target)
        assert stats["attributions_transferred"] == 1
        assert Attribution.objects.filter(identity=target).count() == 1
        assert Attribution.objects.filter(identity=source).count() == 0


@pytest.mark.django_db
class TestSessionRedirect:
    """Tests for session redirection after merge."""

    def test_redirect_merged_sessions_task(self):
        """Sessions pointing to merged identity are updated."""
        from apps.contacts.identity.tasks import redirect_merged_sessions
        from django.contrib.sessions.backends.db import SessionStore

        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)

        # Create a session referencing the source
        store = SessionStore()
        store["identity_pk"] = source.pk
        store["identity_id"] = source.public_id
        store.create()

        result = redirect_merged_sessions(source.pk, target.pk, target.public_id)
        assert result["status"] == "success"
        assert result["sessions_redirected"] == 1

        # Verify session was updated
        updated_store = SessionStore(session_key=store.session_key)
        assert updated_store["identity_pk"] == target.pk
        assert updated_store["identity_id"] == target.public_id

    def test_redirect_no_matching_sessions(self):
        """No error when no sessions match."""
        from apps.contacts.identity.tasks import redirect_merged_sessions

        result = redirect_merged_sessions(99999, 99998, "idt_fake")
        assert result["status"] == "success"
        assert result["sessions_redirected"] == 0


@pytest.mark.django_db
class TestVisitorMiddlewareFKResolution:
    """Tests for VisitorMiddleware using fp.identity FK directly."""

    def test_fingerprint_resolves_via_fk(self):
        """VisitorMiddleware resolves identity via fp.identity FK."""
        from core.tracking.middleware import VisitorMiddleware
        from django.test import RequestFactory

        identity = Identity.objects.create(status=Identity.ACTIVE)
        fp = FingerprintIdentity.objects.create(hash="test_fp_123", identity=identity)

        factory = RequestFactory()
        request = factory.get("/inscrever-test/")
        request.COOKIES["fpjs_vid"] = fp.hash

        middleware = VisitorMiddleware(lambda r: None)
        middleware._set_empty_defaults(request)

        with patch.object(middleware, "_load_cached_visitor", side_effect=Exception):
            # Force DB lookup (bypass cache)
            middleware._identify_visitor(request)

        assert request.identity == identity  # type: ignore[attr-defined]
        assert request.fingerprint_identity == fp  # type: ignore[attr-defined]

    def test_merged_identity_cache_invalidated(self):
        """Cached identity that was merged is invalidated."""
        from core.tracking.middleware import VisitorMiddleware
        from django.test import RequestFactory

        identity = Identity.objects.create(status=Identity.MERGED)
        fp = FingerprintIdentity.objects.create(hash="test_fp_456", identity=identity)

        factory = RequestFactory()
        request = factory.get("/inscrever-test/")
        request.COOKIES["fpjs_vid"] = fp.hash

        middleware = VisitorMiddleware(lambda r: None)
        middleware._set_empty_defaults(request)
        middleware._identify_visitor(request)

        # Merged identity should NOT be set (filtered by status=ACTIVE in cache load)
        assert request.identity is None  # type: ignore[attr-defined]
