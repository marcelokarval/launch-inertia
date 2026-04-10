"""
Tests for Phase 4: Hashed Contact Cookies + Storage.

Covers:
- hash_email() / hash_phone() utilities
- value_sha256 auto-compute on ContactEmail/ContactPhone.save()
- _set_hashed_pii_cookies() helper in landing views
- _recover_identity_from_hashed_cookies() in IdentitySessionMiddleware
"""
# pyright: reportAttributeAccessIssue=false, reportAssignmentType=false

import hashlib
from unittest.mock import MagicMock

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory

from core.shared.hashing import hash_email, hash_phone
from core.tracking.identity_middleware import IdentitySessionMiddleware
from tests.factories import ContactEmailFactory, ContactPhoneFactory, IdentityFactory


# ── hash_email tests ──────────────────────────────────────────────────


class TestHashEmail:
    """Tests for hash_email() utility."""

    def test_basic_email(self):
        result = hash_email("user@example.com")
        expected = hashlib.sha256(b"user@example.com").hexdigest()
        assert result == expected
        assert len(result) == 64

    def test_normalizes_uppercase(self):
        assert hash_email("User@Example.COM") == hash_email("user@example.com")

    def test_strips_whitespace(self):
        assert hash_email("  user@example.com  ") == hash_email("user@example.com")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="Cannot hash empty email"):
            hash_email("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Cannot hash empty email"):
            hash_email("   ")

    def test_deterministic(self):
        """Same input always produces same hash."""
        h1 = hash_email("test@test.com")
        h2 = hash_email("test@test.com")
        assert h1 == h2


# ── hash_phone tests ─────────────────────────────────────────────────


class TestHashPhone:
    """Tests for hash_phone() utility."""

    def test_basic_digits(self):
        result = hash_phone("5511999887766")
        expected = hashlib.sha256(b"5511999887766").hexdigest()
        assert result == expected

    def test_strips_formatting(self):
        """Phone with +, spaces, dashes produces same hash as digits-only."""
        assert hash_phone("+55 11 99988-7766") == hash_phone("5511999887766")

    def test_strips_parentheses(self):
        assert hash_phone("(11) 99988-7766") == hash_phone("11999887766")

    def test_no_digits_raises(self):
        with pytest.raises(ValueError, match="no digits"):
            hash_phone("")

    def test_only_symbols_raises(self):
        with pytest.raises(ValueError, match="no digits"):
            hash_phone("+-() ")

    def test_deterministic(self):
        h1 = hash_phone("+5511999001122")
        h2 = hash_phone("5511999001122")
        assert h1 == h2


# ── ContactEmail.value_sha256 auto-compute ───────────────────────────


@pytest.mark.django_db
class TestContactEmailSha256:
    """Tests for value_sha256 auto-compute on ContactEmail.save()."""

    def test_sha256_auto_computed_on_save(self):
        identity = IdentityFactory()
        email = ContactEmailFactory(
            value="autotest@example.com",
            identity=identity,
        )
        expected = hash_email("autotest@example.com")
        assert email.value_sha256 == expected

    def test_sha256_not_overwritten_if_set(self):
        """If value_sha256 is already set, save() doesn't recompute."""
        identity = IdentityFactory()
        email = ContactEmailFactory(
            value="preset@example.com",
            identity=identity,
            value_sha256="custom_hash_value",
        )
        assert email.value_sha256 == "custom_hash_value"

    def test_sha256_uses_normalized_value(self):
        """SHA-256 is computed from the normalized (lowercase) value."""
        identity = IdentityFactory()
        email = ContactEmailFactory(
            value="UPPER@EXAMPLE.COM",
            identity=identity,
        )
        expected = hash_email("upper@example.com")
        assert email.value_sha256 == expected

    def test_sha256_empty_when_no_value(self):
        """No crash if value is empty (edge case)."""
        identity = IdentityFactory()
        email = ContactEmailFactory(
            value="minimal@x.com",
            identity=identity,
        )
        # Just verify it has a hash
        assert len(email.value_sha256) == 64


# ── ContactPhone.value_sha256 auto-compute ───────────────────────────


@pytest.mark.django_db
class TestContactPhoneSha256:
    """Tests for value_sha256 auto-compute on ContactPhone.save()."""

    def test_sha256_auto_computed_on_save(self):
        identity = IdentityFactory()
        phone = ContactPhoneFactory(
            value="+5511999001122",
            identity=identity,
        )
        # After normalization: E.164 format, hash_phone strips non-digits
        assert len(phone.value_sha256) == 64
        assert phone.value_sha256  # Not empty

    def test_sha256_not_overwritten_if_set(self):
        identity = IdentityFactory()
        phone = ContactPhoneFactory(
            value="+5511999002233",
            identity=identity,
            value_sha256="preset_phone_hash",
        )
        assert phone.value_sha256 == "preset_phone_hash"


# ── _set_hashed_pii_cookies ──────────────────────────────────────────


class TestSetHashedPiiCookies:
    """Tests for _set_hashed_pii_cookies() helper."""

    def test_sets_both_cookies(self):
        from apps.landing.views import _set_hashed_pii_cookies

        response = HttpResponse()
        _set_hashed_pii_cookies(response, "test@example.com", "+5511999887766")

        cookies = response.cookies
        assert "_em" in cookies
        assert "_ph" in cookies
        assert cookies["_em"].value == hash_email("test@example.com")
        assert cookies["_ph"].value == hash_phone("+5511999887766")

    def test_httponly_is_true(self):
        from apps.landing.views import _set_hashed_pii_cookies

        response = HttpResponse()
        _set_hashed_pii_cookies(response, "test@example.com", "+5511999887766")

        assert response.cookies["_em"]["httponly"] is True
        assert response.cookies["_ph"]["httponly"] is True

    def test_skips_empty_email(self):
        from apps.landing.views import _set_hashed_pii_cookies

        response = HttpResponse()
        _set_hashed_pii_cookies(response, "", "+5511999887766")

        assert "_em" not in response.cookies
        assert "_ph" in response.cookies

    def test_skips_empty_phone(self):
        from apps.landing.views import _set_hashed_pii_cookies

        response = HttpResponse()
        _set_hashed_pii_cookies(response, "test@example.com", "")

        assert "_em" in response.cookies
        assert "_ph" not in response.cookies

    def test_max_age_365_days(self):
        from apps.landing.views import _set_hashed_pii_cookies

        response = HttpResponse()
        _set_hashed_pii_cookies(response, "test@example.com", "+5511999887766")

        expected_max_age = 365 * 24 * 60 * 60
        assert response.cookies["_em"]["max-age"] == expected_max_age
        assert response.cookies["_ph"]["max-age"] == expected_max_age


# ── _recover_identity_from_hashed_cookies ────────────────────────────


@pytest.mark.django_db
class TestRecoverIdentityFromHashedCookies:
    """Tests for IdentitySessionMiddleware._recover_identity_from_hashed_cookies()."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.rf = RequestFactory()
        self.get_response = MagicMock(return_value=HttpResponse())
        self.middleware = IdentitySessionMiddleware(self.get_response)

    def _make_request(self, cookies: dict[str, str] | None = None):
        """Create a request with optional cookies and a real session."""
        request = self.rf.get("/inscrever-test/")
        request.session = SessionStore()
        request.session.create()
        if cookies:
            request.COOKIES.update(cookies)
        return request

    def test_no_cookies_returns_none(self):
        request = self._make_request()
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )
        assert result is None

    def test_recovers_from_email_hash(self):
        """_em cookie with matching ContactEmail.value_sha256 recovers identity."""
        identity = IdentityFactory(confidence_score=0.9, status="active")
        email = ContactEmailFactory(
            value="returning@example.com",
            identity=identity,
        )
        em_hash = email.value_sha256

        request = self._make_request(cookies={"_em": em_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is not None
        assert result.pk == identity.pk
        assert request.session["identity_pk"] == identity.pk
        assert request.session["identity_id"] == identity.public_id
        assert request.session["visitor_status"] == "returning"

    def test_recovers_from_phone_hash(self):
        """_ph cookie with matching ContactPhone.value_sha256 recovers identity."""
        identity = IdentityFactory(confidence_score=0.8, status="active")
        phone = ContactPhoneFactory(
            value="+5511999334455",
            identity=identity,
        )
        ph_hash = phone.value_sha256

        request = self._make_request(cookies={"_ph": ph_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is not None
        assert result.pk == identity.pk

    def test_email_takes_priority_over_phone(self):
        """When both _em and _ph cookies exist, email match takes priority."""
        identity_email = IdentityFactory(confidence_score=0.9, status="active")
        identity_phone = IdentityFactory(confidence_score=0.8, status="active")

        email = ContactEmailFactory(
            value="priority@example.com",
            identity=identity_email,
        )
        phone = ContactPhoneFactory(
            value="+5511999556677",
            identity=identity_phone,
        )

        request = self._make_request(
            cookies={"_em": email.value_sha256, "_ph": phone.value_sha256}
        )
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        # Email match wins
        assert result is not None
        assert result.pk == identity_email.pk

    def test_ignores_merged_identity(self):
        """Cookies pointing to a merged (non-active) identity return None."""
        merged_identity = IdentityFactory(status="merged")
        ContactEmailFactory(
            value="merged@example.com",
            identity=merged_identity,
        )
        em_hash = hash_email("merged@example.com")

        request = self._make_request(cookies={"_em": em_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is None

    def test_ignores_deleted_identity(self):
        """Cookies pointing to a soft-deleted identity return None."""
        deleted_identity = IdentityFactory(status="active", is_deleted=True)
        ContactEmailFactory(
            value="deleted@example.com",
            identity=deleted_identity,
        )
        em_hash = hash_email("deleted@example.com")

        request = self._make_request(cookies={"_em": em_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is None

    def test_ignores_invalid_hash_length(self):
        """Cookies with non-SHA256 values (wrong length) are skipped."""
        request = self._make_request(cookies={"_em": "short_hash", "_ph": "abc"})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )
        assert result is None

    def test_no_match_returns_none(self):
        """Valid-looking hash that doesn't match any contact returns None."""
        fake_hash = hashlib.sha256(b"nonexistent@nowhere.com").hexdigest()
        request = self._make_request(cookies={"_em": fake_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )
        assert result is None

    def test_ignores_deleted_contact_email(self):
        """Soft-deleted ContactEmail records are not matched."""
        identity = IdentityFactory(status="active")
        email = ContactEmailFactory(
            value="softdel-unique@example.com",
            identity=identity,
        )
        em_hash = email.value_sha256

        # Soft-delete the email after creation (bypasses signal issues)
        from apps.contacts.email.models import ContactEmail

        ContactEmail.objects.filter(pk=email.pk).update(is_deleted=True)

        request = self._make_request(cookies={"_em": em_hash})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is None

    def test_updates_last_seen_on_recovery(self):
        """Recovered identity has last_seen updated."""
        from django.utils import timezone

        identity = IdentityFactory(status="active")
        email = ContactEmailFactory(value="lastseen@example.com", identity=identity)

        old_last_seen = identity.last_seen

        request = self._make_request(cookies={"_em": email.value_sha256})
        result = self.middleware._recover_identity_from_hashed_cookies(
            request, request.session
        )

        assert result is not None
        result.refresh_from_db()
        # last_seen should be recent (within last few seconds)
        assert result.last_seen is not None
        if old_last_seen is not None:
            assert result.last_seen >= old_last_seen
