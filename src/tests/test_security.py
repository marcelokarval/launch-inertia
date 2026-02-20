"""
Unit tests for security decorators: require_ownership.
"""
# pyright: reportAttributeAccessIssue=false

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
from apps.notifications.models import Notification
from tests.factories import UserFactory, NotificationFactory


class TestRequireOwnershipDecorator:
    """Tests for @require_ownership decorator."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.rf = RequestFactory()
        self.user = UserFactory(email="owner@test.com")
        self.other = UserFactory(email="intruder@test.com")
        self.notification = NotificationFactory(recipient=self.user)

    def _make_view(self):
        """Create a simple view wrapped with @require_ownership."""

        @require_ownership(Notification, owner_field="recipient")
        def view(request, public_id):
            return MagicMock(status_code=200)

        return view

    def test_owner_can_access(self):
        view = self._make_view()
        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = self.user

        response = view(request, public_id=self.notification.public_id)
        assert response.status_code == 200
        assert request.verified_object == self.notification

    def test_non_owner_gets_permission_denied(self):
        view = self._make_view()
        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = self.other
        request.META["REMOTE_ADDR"] = "1.2.3.4"

        with pytest.raises(RequireOwnershipError):
            view(request, public_id=self.notification.public_id)

    def test_nonexistent_object_raises_404(self):
        view = self._make_view()
        request = self.rf.get("/app/notifications/ntf_nonexistent/")
        request.user = self.user

        with pytest.raises(Http404):
            view(request, public_id="ntf_nonexistent")

    def test_staff_can_access_others_notification(self):
        staff = UserFactory(email="staffaccess@test.com", staff=True)
        view = self._make_view()
        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = staff

        response = view(request, public_id=self.notification.public_id)
        assert response.status_code == 200

    def test_superuser_can_access_others_notification(self):
        admin = UserFactory(email="superaccess@test.com", superuser=True)
        view = self._make_view()
        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = admin

        response = view(request, public_id=self.notification.public_id)
        assert response.status_code == 200

    def test_staff_bypass_can_be_disabled(self):
        staff = UserFactory(email="nobypass@test.com", staff=True)

        @require_ownership(
            Notification,
            owner_field="recipient",
            allow_staff=False,
            allow_superuser=False,
        )
        def view(request, public_id):
            return MagicMock(status_code=200)

        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = staff
        request.META["REMOTE_ADDR"] = "1.2.3.4"

        with pytest.raises(RequireOwnershipError):
            view(request, public_id=self.notification.public_id)

    def test_verified_object_attached_to_request(self):
        view = self._make_view()
        request = self.rf.get(f"/app/notifications/{self.notification.public_id}/")
        request.user = self.user

        view(request, public_id=self.notification.public_id)
        assert hasattr(request, "verified_object")
        assert request.verified_object.pk == self.notification.pk


class TestGetOwnedObjectOr404:
    """Tests for get_owned_object_or_404() utility."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="util@test.com")
        self.other = UserFactory(email="utilother@test.com")
        self.notification = NotificationFactory(recipient=self.user)

    def test_owner_gets_object(self):
        obj = get_owned_object_or_404(
            Notification,
            self.user,
            owner_field="recipient",
            public_id=self.notification.public_id,
        )
        assert obj.pk == self.notification.pk

    def test_non_owner_gets_denied(self):
        with pytest.raises(PermissionDenied):
            get_owned_object_or_404(
                Notification,
                self.other,
                owner_field="recipient",
                public_id=self.notification.public_id,
            )

    def test_nonexistent_raises_404(self):
        with pytest.raises(Http404):
            get_owned_object_or_404(
                Notification,
                self.user,
                owner_field="recipient",
                public_id="ntf_nonexistent",
            )

    def test_staff_can_access(self):
        staff = UserFactory(email="staffutil@test.com", staff=True)
        obj = get_owned_object_or_404(
            Notification,
            staff,
            owner_field="recipient",
            public_id=self.notification.public_id,
        )
        assert obj.pk == self.notification.pk
