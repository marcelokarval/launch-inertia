"""
Unit tests for security decorators: require_ownership.
"""

import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory
from django.http import Http404
from django.core.exceptions import PermissionDenied

from core.security.decorators.ownership import (
    require_ownership,
    get_owned_object_or_404,
    RequireOwnershipError,
)
from apps.contacts.models import Contact
from tests.factories import UserFactory, ContactFactory


class TestRequireOwnershipDecorator:
    """Tests for @require_ownership decorator."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.rf = RequestFactory()
        self.user = UserFactory(email="owner@test.com")
        self.other = UserFactory(email="intruder@test.com")
        self.contact = ContactFactory(owner=self.user, created_by=self.user)

    def _make_view(self):
        """Create a simple view wrapped with @require_ownership."""

        @require_ownership(Contact, owner_field="owner")
        def view(request, public_id):
            return MagicMock(status_code=200)

        return view

    def test_owner_can_access(self):
        view = self._make_view()
        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = self.user

        response = view(request, public_id=self.contact.public_id)
        assert response.status_code == 200
        assert request.verified_object == self.contact

    def test_non_owner_gets_permission_denied(self):
        view = self._make_view()
        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = self.other
        request.META["REMOTE_ADDR"] = "1.2.3.4"

        with pytest.raises(RequireOwnershipError):
            view(request, public_id=self.contact.public_id)

    def test_nonexistent_object_raises_404(self):
        view = self._make_view()
        request = self.rf.get("/contacts/con_nonexistent/")
        request.user = self.user

        with pytest.raises(Http404):
            view(request, public_id="con_nonexistent")

    def test_staff_can_access_others_contact(self):
        staff = UserFactory(email="staffaccess@test.com", staff=True)
        view = self._make_view()
        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = staff

        response = view(request, public_id=self.contact.public_id)
        assert response.status_code == 200

    def test_superuser_can_access_others_contact(self):
        admin = UserFactory(email="superaccess@test.com", superuser=True)
        view = self._make_view()
        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = admin

        response = view(request, public_id=self.contact.public_id)
        assert response.status_code == 200

    def test_staff_bypass_can_be_disabled(self):
        staff = UserFactory(email="nobypass@test.com", staff=True)

        @require_ownership(
            Contact, owner_field="owner", allow_staff=False, allow_superuser=False
        )
        def view(request, public_id):
            return MagicMock(status_code=200)

        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = staff
        request.META["REMOTE_ADDR"] = "1.2.3.4"

        with pytest.raises(RequireOwnershipError):
            view(request, public_id=self.contact.public_id)

    def test_verified_object_attached_to_request(self):
        view = self._make_view()
        request = self.rf.get(f"/contacts/{self.contact.public_id}/")
        request.user = self.user

        view(request, public_id=self.contact.public_id)
        assert hasattr(request, "verified_object")
        assert request.verified_object.pk == self.contact.pk


class TestGetOwnedObjectOr404:
    """Tests for get_owned_object_or_404() utility."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="util@test.com")
        self.other = UserFactory(email="utilother@test.com")
        self.contact = ContactFactory(owner=self.user, created_by=self.user)

    def test_owner_gets_object(self):
        obj = get_owned_object_or_404(
            Contact, self.user, public_id=self.contact.public_id
        )
        assert obj.pk == self.contact.pk

    def test_non_owner_gets_denied(self):
        with pytest.raises(PermissionDenied):
            get_owned_object_or_404(
                Contact, self.other, public_id=self.contact.public_id
            )

    def test_nonexistent_raises_404(self):
        with pytest.raises(Http404):
            get_owned_object_or_404(Contact, self.user, public_id="con_nonexistent")

    def test_staff_can_access(self):
        staff = UserFactory(email="staffutil@test.com", staff=True)
        obj = get_owned_object_or_404(Contact, staff, public_id=self.contact.public_id)
        assert obj.pk == self.contact.pk
