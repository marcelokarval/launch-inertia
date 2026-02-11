"""
Tests for the contact identity resolution system.

Tests the 4 sub-apps:
- contacts.email: ContactEmail model + EmailService
- contacts.phone: ContactPhone model + PhoneService
- contacts.fingerprint: FingerprintIdentity/Event/Contact models + services
- contacts.identity: Identity/IdentityHistory models + resolution/merge/analysis services
"""

import pytest
from django.utils import timezone

from apps.contacts.email.models import ContactEmail
from apps.contacts.email.services.email_service import EmailService
from apps.contacts.email.services.verification_service import VerificationService
from apps.contacts.phone.models import ContactPhone
from apps.contacts.phone.services.phone_service import PhoneService
from apps.contacts.fingerprint.models import (
    FingerprintIdentity,
    FingerprintEvent,
    FingerprintContact,
)
from apps.contacts.fingerprint.services.fingerprint_service import FingerprintService
from apps.contacts.fingerprint.services.payload_service import PayloadService
from apps.contacts.identity.models import Identity, IdentityHistory
from apps.contacts.identity.services.identity_service import IdentityService
from apps.contacts.identity.services.merge_service import (
    MergeService,
    MergeValidationError,
)
from apps.contacts.identity.services.resolution_service import ResolutionService
from apps.contacts.identity.services.analysis_service import AnalysisService


# ═══════════════════════════════════════════════════════════════════════
# EMAIL TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestContactEmail:
    """Tests for ContactEmail model."""

    def test_create_email_normalizes(self):
        email = ContactEmail.objects.create(value="  Test@GMAIL.COM  ")
        assert email.value == "test@gmail.com"
        assert email.domain == "gmail.com"
        assert email.original_value == "  Test@GMAIL.COM  "

    def test_create_email_generates_public_id(self):
        email = ContactEmail.objects.create(value="john@example.com")
        assert email.public_id.startswith("cem_")
        assert len(email.public_id) > 4

    def test_email_verify(self):
        email = ContactEmail.objects.create(value="verify@example.com")
        assert not email.is_verified
        email.verify()
        email.refresh_from_db()
        assert email.is_verified
        assert email.verified_at is not None

    def test_email_unverify(self):
        email = ContactEmail.objects.create(value="unverify@example.com")
        email.verify()
        email.unverify()
        email.refresh_from_db()
        assert not email.is_verified
        assert email.verified_at is None

    def test_email_to_dict(self):
        email = ContactEmail.objects.create(value="dict@example.com")
        data = email.to_dict()
        assert data["value"] == "dict@example.com"
        assert data["domain"] == "example.com"
        assert data["is_verified"] is False
        assert "id" in data  # public_id

    def test_email_unique_value(self):
        ContactEmail.objects.create(value="unique@example.com")
        with pytest.raises(Exception):
            ContactEmail.objects.create(value="unique@example.com")

    def test_is_valid_email(self):
        assert ContactEmail.is_valid_email("test@example.com")
        assert ContactEmail.is_valid_email("user.name+tag@domain.co.uk")
        assert not ContactEmail.is_valid_email("invalid")
        assert not ContactEmail.is_valid_email("@domain.com")


@pytest.mark.django_db
class TestEmailService:
    """Tests for EmailService."""

    def test_get_or_create_email_creates(self):
        service = EmailService()
        email, created = service.get_or_create_email("new@example.com")
        assert created
        assert email.value == "new@example.com"
        assert email.domain == "example.com"

    def test_get_or_create_email_gets_existing(self):
        service = EmailService()
        email1, created1 = service.get_or_create_email("existing@example.com")
        email2, created2 = service.get_or_create_email("existing@example.com")
        assert created1
        assert not created2
        assert email1.pk == email2.pk

    def test_get_or_create_normalizes(self):
        service = EmailService()
        email, _ = service.get_or_create_email("  UPPER@EXAMPLE.COM  ")
        assert email.value == "upper@example.com"

    def test_verify_email(self):
        service = EmailService()
        email, _ = service.get_or_create_email("toverify@example.com")
        service.verify_email(email)
        email.refresh_from_db()
        assert email.is_verified

    def test_process_email_bounce(self):
        service = EmailService()
        email, _ = service.get_or_create_email("bounce@example.com")
        email.verify()
        service.process_email_bounce(email, {"type": "hard", "reason": "invalid"})
        email.refresh_from_db()
        assert not email.is_verified
        assert email.get_metadata("bounce_data") == {
            "type": "hard",
            "reason": "invalid",
        }

    def test_get_email_by_value(self):
        service = EmailService()
        service.get_or_create_email("findme@example.com")
        found = service.get_email_by_value("findme@example.com")
        assert found is not None
        assert found.value == "findme@example.com"

    def test_is_disposable_email(self):
        assert EmailService.is_disposable_email("test@tempmail.com")
        assert not EmailService.is_disposable_email("test@gmail.com")


@pytest.mark.django_db
class TestVerificationService:
    """Tests for VerificationService."""

    def test_generate_verification_code(self):
        code = VerificationService.generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_verification_token(self):
        token = VerificationService.generate_verification_token()
        assert len(token) == 32
        assert token.isalnum()

    def test_send_and_verify_email_with_code(self):
        email = ContactEmail.objects.create(value="verify_code@example.com")
        result = VerificationService.send_email_verification(email)
        code = result["code"]

        success = VerificationService.verify_email_with_code(email, code)
        assert success
        email.refresh_from_db()
        assert email.is_verified

    def test_verify_email_wrong_code(self):
        email = ContactEmail.objects.create(value="wrong_code@example.com")
        VerificationService.send_email_verification(email)
        assert not VerificationService.verify_email_with_code(email, "000000")

    def test_send_and_verify_phone(self):
        phone = ContactPhone.objects.create(value="+5511999998888")
        result = VerificationService.send_phone_verification(phone)
        code = result["code"]

        success = VerificationService.verify_phone_with_code(phone, code)
        assert success
        phone.refresh_from_db()
        assert phone.is_verified


# ═══════════════════════════════════════════════════════════════════════
# PHONE TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestContactPhone:
    """Tests for ContactPhone model."""

    def test_create_phone_generates_public_id(self):
        phone = ContactPhone.objects.create(value="+5511999887766")
        assert phone.public_id.startswith("cph_")

    def test_phone_type_detection_mobile(self):
        phone = ContactPhone(value="+5511999887766")
        assert phone.detect_type() == "mobile"

    def test_phone_type_detection_landline(self):
        phone = ContactPhone(value="+551133445566")
        assert phone.detect_type() == "landline"

    def test_phone_format_for_display_mobile(self):
        phone = ContactPhone.objects.create(value="+5511999887766")
        display = phone.format_for_display()
        assert display == "(11) 99988-7766"

    def test_phone_format_for_display_landline(self):
        phone = ContactPhone.objects.create(value="+551133445566")
        display = phone.format_for_display()
        assert display == "(11) 3344-5566"

    def test_phone_verify(self):
        phone = ContactPhone.objects.create(value="+5511988776655")
        phone.verify()
        phone.refresh_from_db()
        assert phone.is_verified
        assert phone.verified_at is not None

    def test_phone_to_dict(self):
        phone = ContactPhone.objects.create(value="+5511977665544")
        data = phone.to_dict()
        assert data["value"] == "+5511977665544"
        assert "display_value" in data
        assert data["is_verified"] is False


@pytest.mark.django_db
class TestPhoneService:
    """Tests for PhoneService."""

    def test_get_or_create_phone_creates(self):
        service = PhoneService()
        phone, created = service.get_or_create_phone("+5511999001122")
        assert created
        assert phone.value.startswith("+")

    def test_get_or_create_phone_gets_existing(self):
        service = PhoneService()
        p1, c1 = service.get_or_create_phone("+5511999002233")
        p2, c2 = service.get_or_create_phone("+5511999002233")
        assert c1
        assert not c2
        assert p1.pk == p2.pk

    def test_normalize_phone(self):
        result = PhoneService.normalize_phone("11999887766")
        assert result == "+5511999887766"

    def test_detect_phone_type(self):
        assert PhoneService.detect_phone_type("+5511999887766") == "mobile"
        assert PhoneService.detect_phone_type("+551133445566") == "landline"


# ═══════════════════════════════════════════════════════════════════════
# FINGERPRINT TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestFingerprintIdentity:
    """Tests for FingerprintIdentity model."""

    def test_create_fingerprint(self):
        fp = FingerprintIdentity.objects.create(
            hash="abc123def456ghi789jkl012mno345pq",
            confidence_score=0.95,
            device_type="desktop",
        )
        assert fp.public_id.startswith("fpi_")
        assert fp.confidence_score == 0.95

    def test_get_browser_family(self):
        fp = FingerprintIdentity(browser="Chrome Mobile")
        assert fp.get_browser_family() == "Chrome"

        fp2 = FingerprintIdentity(browser="Firefox")
        assert fp2.get_browser_family() == "Firefox"

    def test_is_mobile_device(self):
        fp = FingerprintIdentity(device_type="mobile")
        assert fp.is_mobile_device()

        fp2 = FingerprintIdentity(device_type="desktop")
        assert not fp2.is_mobile_device()

    def test_fraud_signals_incognito(self):
        fp = FingerprintIdentity(
            hash="test_incognito_hash",
            browser_info={"incognito": True},
            confidence_score=0.9,
        )
        signals = fp.get_fraud_signals()
        assert any(s["type"] == "incognito" for s in signals)

    def test_fraud_signals_low_confidence(self):
        fp = FingerprintIdentity(
            hash="test_low_conf_hash",
            confidence_score=0.3,
        )
        signals = fp.get_fraud_signals()
        assert any(s["type"] == "low_confidence" for s in signals)


@pytest.mark.django_db
class TestFingerprintService:
    """Tests for FingerprintService."""

    def test_get_or_create_fingerprint_creates(self):
        service = FingerprintService()
        fp, created = service.get_or_create_fingerprint(
            {
                "hash": "service_test_hash_001",
                "confidence_score": 0.88,
                "device_type": "desktop",
                "browser": "Chrome",
            }
        )
        assert created
        assert fp.hash == "service_test_hash_001"
        assert fp.confidence_score == 0.88

    def test_get_or_create_fingerprint_gets_existing(self):
        service = FingerprintService()
        fp1, c1 = service.get_or_create_fingerprint({"hash": "existing_hash_001"})
        fp2, c2 = service.get_or_create_fingerprint({"hash": "existing_hash_001"})
        assert c1
        assert not c2
        assert fp1.pk == fp2.pk

    def test_get_or_create_requires_hash(self):
        service = FingerprintService()
        with pytest.raises(ValueError):
            service.get_or_create_fingerprint({})


@pytest.mark.django_db
class TestFingerprintEvent:
    """Tests for FingerprintEvent model."""

    def test_record_pageview(self):
        fp = FingerprintIdentity.objects.create(hash="event_test_hash_001")
        event = FingerprintEvent.record_pageview(fp, "https://example.com/page")
        assert event.event_type == "page_view"
        assert event.page_url == "https://example.com/page"
        assert event.fingerprint == fp

    def test_record_form_submission(self):
        fp = FingerprintIdentity.objects.create(hash="form_test_hash_001")
        event = FingerprintEvent.record_form_submission(
            fp, "https://example.com/form", {"email": "test@test.com"}
        )
        assert event.event_type == "form_submit"
        assert event.user_data["email"] == "test@test.com"


@pytest.mark.django_db
class TestPayloadService:
    """Tests for PayloadService."""

    def test_process_fingerprintjs_payload(self):
        payload = {
            "requestId": "req_123",
            "visitorId": "visitor_abc123",
            "visitorFound": True,
            "confidence": {"score": 0.97},
            "visits": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "url": "https://example.com",
                    "ip": "1.2.3.4",
                    "incognito": False,
                    "browserDetails": {
                        "browserName": "Chrome",
                        "browserMajorVersion": "120",
                        "browserFullVersion": "120.0.1",
                        "browserEngine": "Blink",
                        "os": "Windows",
                        "osVersion": "11",
                        "device": "Desktop",
                        "userAgent": "Mozilla/5.0...",
                    },
                    "ipLocation": {
                        "country": {"name": "Brazil", "code": "BR"},
                        "city": {"name": "São Paulo"},
                        "latitude": -23.5,
                        "longitude": -46.6,
                        "timezone": "America/Sao_Paulo",
                    },
                }
            ],
        }

        fp_data, ctx_data = PayloadService.process_fingerprintjs_payload(payload)

        assert fp_data["hash"] == "visitor_abc123"
        assert fp_data["confidence_score"] == 0.97
        assert fp_data["device_type"] == "desktop"
        assert fp_data["browser"] == "Chrome"
        assert fp_data["os"] == "Windows"
        assert fp_data["geo_info"]["country"] == "Brazil"
        assert ctx_data["request_id"] == "req_123"

    def test_classify_device_type(self):
        assert PayloadService.classify_device_type({"device": "Mobile"}) == "mobile"
        assert PayloadService.classify_device_type({"device": "Desktop"}) == "desktop"
        assert PayloadService.classify_device_type({"os": "iOS"}) == "mobile"
        assert PayloadService.classify_device_type({}) == "unknown"

    def test_fraud_detection(self):
        signals = PayloadService.detect_fraud_patterns(
            {
                "browser_info": {"incognito": True},
                "confidence_score": 0.3,
            }
        )
        assert len(signals) == 2  # incognito + low confidence

    def test_fraud_score_calculation(self):
        signals = [
            {"type": "incognito", "severity": "medium"},
            {"type": "low_confidence", "severity": "high"},
        ]
        score = PayloadService.calculate_fraud_score(signals)
        assert score == pytest.approx(0.45)  # 0.15 + 0.30

    def test_fraud_recommendation(self):
        assert PayloadService.get_fraud_recommendation(0.8) == "block"
        assert PayloadService.get_fraud_recommendation(0.5) == "review"
        assert PayloadService.get_fraud_recommendation(0.2) == "allow"


# ═══════════════════════════════════════════════════════════════════════
# IDENTITY TESTS
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestIdentityModel:
    """Tests for Identity model."""

    def test_create_identity(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        assert identity.public_id.startswith("idt_")
        assert identity.status == "active"

    def test_mark_as_merged(self):
        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)
        source.mark_as_merged(target)
        source.refresh_from_db()
        assert source.status == Identity.MERGED
        assert source.merged_into == target

    def test_get_merged_identities(self):
        target = Identity.objects.create(status=Identity.ACTIVE)
        src1 = Identity.objects.create(status=Identity.ACTIVE)
        src2 = Identity.objects.create(status=Identity.ACTIVE)
        src1.mark_as_merged(target)
        src2.mark_as_merged(target)
        merged = target.get_merged_identities()
        assert merged.count() == 2

    def test_to_dict(self):
        identity = Identity.objects.create(
            status=Identity.ACTIVE,
            first_seen_source="test",
        )
        data = identity.to_dict()
        assert data["status"] == "active"
        assert data["first_seen_source"] == "test"
        assert "email_count" in data


@pytest.mark.django_db
class TestIdentityService:
    """Tests for IdentityService."""

    def test_create_identity(self):
        service = IdentityService()
        identity = service.create_identity(source="test")
        assert identity.status == Identity.ACTIVE
        assert identity.first_seen_source == "test"
        # Service creates 1 history entry, signal triggers tasks that
        # create additional entries (confidence update, history update, graph)
        assert identity.history.count() >= 1

    def test_calculate_confidence_score(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        # No contacts/fingerprints -> base score (0.10 from ConfidenceEngine)
        score = IdentityService.calculate_confidence_score(identity)
        assert score == 0.10

    def test_calculate_confidence_with_verified_email(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        email = ContactEmail.objects.create(
            value="scored@example.com",
            identity=identity,
            is_verified=True,
        )
        score = IdentityService.calculate_confidence_score(identity)
        # ConfidenceEngine: 0.10 base + 0.15 verified email = 0.25
        assert score == 0.25

    def test_update_identity_status(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        IdentityService.update_identity_status(identity, Identity.INACTIVE)
        identity.refresh_from_db()
        assert identity.status == Identity.INACTIVE
        assert identity.history.filter(
            operation_type=IdentityHistory.STATUS_CHANGE
        ).exists()


@pytest.mark.django_db
class TestMergeService:
    """Tests for MergeService."""

    def test_validate_merge_same_identity(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        with pytest.raises(
            MergeValidationError, match="Cannot merge an identity into itself"
        ):
            MergeService.validate_merge_conditions(identity, identity)

    def test_validate_merge_inactive_source(self):
        source = Identity.objects.create(status=Identity.INACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)
        with pytest.raises(MergeValidationError, match="not active"):
            MergeService.validate_merge_conditions(source, target)

    def test_execute_merge(self):
        source = Identity.objects.create(status=Identity.ACTIVE)
        target = Identity.objects.create(status=Identity.ACTIVE)

        # Add contacts to source
        ContactEmail.objects.create(value="merge_email@example.com", identity=source)
        ContactPhone.objects.create(value="+5511999001100", identity=source)
        FingerprintIdentity.objects.create(hash="merge_fp_hash_001", identity=source)

        stats = MergeService.execute_merge(source, target)

        assert stats["emails_transferred"] == 1
        assert stats["phones_transferred"] == 1
        assert stats["fingerprints_transferred"] == 1

        source.refresh_from_db()
        assert source.status == Identity.MERGED
        assert source.merged_into == target

        # Verify relationships moved
        assert target.email_contacts.count() == 1
        assert target.phone_contacts.count() == 1
        assert target.fingerprints.count() == 1

    def test_find_merge_candidates_no_shared_data(self):
        """With unique constraints, no two identities share the same contact."""
        identity1 = Identity.objects.create(status=Identity.ACTIVE)
        identity2 = Identity.objects.create(status=Identity.ACTIVE)

        # Different emails/phones on each identity
        ContactEmail.objects.create(value="candidate1@example.com", identity=identity1)
        ContactEmail.objects.create(value="candidate2@example.com", identity=identity2)

        candidates = MergeService.find_merge_candidates(identity1)
        # No shared values -> no candidates
        assert len(candidates) == 0

    def test_auto_merge_no_candidates(self):
        """Auto-merge with no candidates does nothing."""
        identity = Identity.objects.create(status=Identity.ACTIVE)
        results = MergeService.auto_merge_identities(identity)
        assert len(results) == 0


@pytest.mark.django_db
class TestResolutionService:
    """Tests for ResolutionService (the crown jewel)."""

    def test_resolve_anonymous_identity(self):
        """Fingerprint only, no contacts -> anonymous identity."""
        result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data={"hash": "anon_test_hash_001", "confidence_score": 0.9},
        )
        assert result["is_anonymous"] is True
        assert result["identity_id"].startswith("idt_")
        assert result["fingerprint_id"].startswith("fpi_")

    def test_resolve_new_identity_with_email(self):
        """New fingerprint + new email -> new identity."""
        result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data={"hash": "new_email_hash_001", "confidence_score": 0.9},
            contact_data={"email": "newuser@example.com"},
        )
        assert result["is_new"] is True
        assert result["is_anonymous"] is False

        # Verify identity was created with email
        identity = Identity.objects.get(public_id=result["identity_id"])
        assert identity.email_contacts.count() == 1
        assert identity.email_contacts.first().value == "newuser@example.com"

    def test_resolve_new_identity_with_email_and_phone(self):
        """New fingerprint + email + phone -> new identity with both."""
        result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data={
                "hash": "full_contact_hash_001",
                "confidence_score": 0.95,
            },
            contact_data={
                "email": "fullcontact@example.com",
                "phone": "+5511999112233",
            },
        )
        assert result["is_new"] is True

        identity = Identity.objects.get(public_id=result["identity_id"])
        assert identity.email_contacts.count() == 1
        assert identity.phone_contacts.count() == 1

    def test_resolve_existing_identity_by_email(self):
        """Known email from a new device -> associate to existing identity."""
        # Create existing identity with email
        existing = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(value="returning@example.com", identity=existing)

        # Resolve with same email from different fingerprint
        result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data={"hash": "new_device_hash_001", "confidence_score": 0.85},
            contact_data={"email": "returning@example.com"},
        )

        assert result["is_new"] is False
        assert result["identity_id"] == existing.public_id

        # Fingerprint should be linked
        assert existing.fingerprints.count() == 1

    def test_resolve_merges_when_multiple_identities_found(self):
        """Email matches identity A, phone matches identity B -> merge."""
        identity_a = Identity.objects.create(status=Identity.ACTIVE)
        identity_b = Identity.objects.create(status=Identity.ACTIVE)

        ContactEmail.objects.create(
            value="multi_email@example.com", identity=identity_a
        )
        ContactPhone.objects.create(value="+5511999334455", identity=identity_b)

        result = ResolutionService.resolve_identity_from_real_data(
            fingerprint_data={
                "hash": "merge_trigger_hash_001",
                "confidence_score": 0.9,
            },
            contact_data={
                "email": "multi_email@example.com",
                "phone": "+5511999334455",
            },
        )

        assert result["is_new"] is False
        assert "merged_count" in result

    def test_confidence_scoring_initial(self):
        fp = FingerprintIdentity(confidence_score=0.9)
        score = ResolutionService.calculate_initial_confidence_score(
            fp, {"email": "test@test.com", "phone": "+5511999000000"}
        )
        # ConfidenceEngine.calculate_initial:
        # 0.10 (base) + 0.9*0.30 (fp) + 0.05 (email) + 0.10 (phone) = 0.52
        assert score == 0.52


@pytest.mark.django_db
class TestAnalysisService:
    """Tests for AnalysisService."""

    def test_analyze_identity_graph(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        ContactEmail.objects.create(
            value="analysis@example.com",
            identity=identity,
            is_verified=True,
        )
        fp = FingerprintIdentity.objects.create(
            hash="analysis_fp_hash_001",
            identity=identity,
            device_type="desktop",
            browser="Chrome",
        )
        FingerprintEvent.record_pageview(fp, "https://example.com/page1")

        analysis = AnalysisService.analyze_identity_graph(identity)

        assert analysis["contacts"]["emails"]["total"] == 1
        assert analysis["contacts"]["emails"]["verified"] == 1
        assert analysis["devices"]["fingerprint_count"] == 1
        assert "desktop" in analysis["devices"]["device_types"]
        assert analysis["activity"]["total_events"] == 1

    def test_find_similar_identities(self):
        identity1 = Identity.objects.create(status=Identity.ACTIVE)
        identity2 = Identity.objects.create(status=Identity.ACTIVE)

        # Share an email between them (via unique constraint, use different values)
        # Actually, emails must be unique. So we use different emails
        # linked to different identities and test for no similarity
        ContactEmail.objects.create(value="similar1@example.com", identity=identity1)
        ContactEmail.objects.create(value="similar2@example.com", identity=identity2)

        similar = AnalysisService.find_similar_identities(identity1)
        assert len(similar) == 0  # No shared values

    def test_get_identity_timeline(self):
        identity = Identity.objects.create(status=Identity.ACTIVE)
        fp = FingerprintIdentity.objects.create(
            hash="timeline_fp_hash_001",
            identity=identity,
            device_type="mobile",
            browser="Safari",
        )
        FingerprintEvent.record_pageview(fp, "https://example.com/page1")
        FingerprintEvent.record_pageview(fp, "https://example.com/page2")

        timeline = AnalysisService.get_identity_timeline(identity)
        assert len(timeline) == 2
        assert timeline[0]["device_type"] == "mobile"
        assert timeline[0]["browser"] == "Safari"
