"""
Unit tests for ContactService CRUD and ownership scoping.
"""

import pytest
from django.http import Http404

from apps.contacts.services.contact_service import ContactService
from tests.factories import UserFactory, ContactFactory


class TestContactServiceList:
    """Tests for ContactService.list_contacts()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="contacts@test.com")
        self.other = UserFactory(email="other@test.com")
        self.service = ContactService(user=self.user)

    def test_list_returns_only_owned_contacts(self):
        ContactFactory.create_batch(3, owner=self.user, created_by=self.user)
        ContactFactory.create_batch(2, owner=self.other, created_by=self.other)

        result = self.service.list_contacts()
        assert len(result["items"]) == 3

    def test_list_empty(self):
        result = self.service.list_contacts()
        assert len(result["items"]) == 0

    def test_list_pagination(self):
        ContactFactory.create_batch(10, owner=self.user, created_by=self.user)

        result = self.service.list_contacts(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["pages"] == 4

    def test_list_search(self):
        ContactFactory(name="John Smith", owner=self.user, created_by=self.user)
        ContactFactory(name="Jane Doe", owner=self.user, created_by=self.user)

        result = self.service.list_contacts(search_query="John")
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "John Smith"

    def test_list_search_by_email(self):
        ContactFactory(
            name="Alice",
            email="alice@example.com",
            owner=self.user,
            created_by=self.user,
        )
        ContactFactory(name="Bob", owner=self.user, created_by=self.user)

        result = self.service.list_contacts(search_query="alice@example")
        assert len(result["items"]) == 1


class TestContactServiceCreate:
    """Tests for ContactService.create_contact()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="creator@test.com")
        self.service = ContactService(user=self.user)

    def test_create_success(self):
        contact, errors = self.service.create_contact(
            {
                "name": "New Contact",
                "email": "new@example.com",
                "phone": "123456789",
            }
        )
        assert errors is None
        assert contact is not None
        assert contact.name == "New Contact"
        assert contact.owner == self.user
        assert contact.created_by == self.user

    def test_create_missing_name(self):
        contact, errors = self.service.create_contact(
            {
                "email": "test@example.com",
            }
        )
        assert contact is None
        assert errors is not None

    def test_create_minimal(self):
        contact, errors = self.service.create_contact(
            {
                "name": "Minimal Contact",
            }
        )
        assert errors is None
        assert contact.name == "Minimal Contact"


class TestContactServiceUpdate:
    """Tests for ContactService.update_contact()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="updater@test.com")
        self.service = ContactService(user=self.user)
        self.contact = ContactFactory(
            name="Original",
            owner=self.user,
            created_by=self.user,
        )

    def test_update_success(self):
        contact, errors = self.service.update_contact(
            self.contact.public_id,
            {"name": "Updated Name"},
        )
        assert errors is None
        assert contact.name == "Updated Name"

    def test_update_nonexistent(self):
        with pytest.raises(Http404):
            self.service.update_contact("con_nonexistent", {"name": "X"})

    def test_update_other_users_contact(self):
        """Cannot update contact owned by another user."""
        other = UserFactory(email="otherowner@test.com")
        their_contact = ContactFactory(owner=other, created_by=other)

        with pytest.raises(Http404):
            self.service.update_contact(
                their_contact.public_id,
                {"name": "Hacked"},
            )


class TestContactServiceDelete:
    """Tests for ContactService.delete_contact()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="deleter@test.com")
        self.service = ContactService(user=self.user)
        self.contact = ContactFactory(
            name="To Delete",
            owner=self.user,
            created_by=self.user,
        )

    def test_delete_success(self):
        name = self.service.delete_contact(self.contact.public_id)
        assert name == "To Delete"

    def test_delete_nonexistent(self):
        with pytest.raises(Http404):
            self.service.delete_contact("con_nonexistent")

    def test_delete_other_users_contact(self):
        """Cannot delete contact owned by another user."""
        other = UserFactory(email="otherown@test.com")
        their_contact = ContactFactory(owner=other, created_by=other)

        with pytest.raises(Http404):
            self.service.delete_contact(their_contact.public_id)


class TestContactServiceGet:
    """Tests for ContactService.get_contact()."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = UserFactory(email="getter@test.com")
        self.service = ContactService(user=self.user)
        self.contact = ContactFactory(owner=self.user, created_by=self.user)

    def test_get_own_contact(self):
        contact = self.service.get_contact(self.contact.public_id)
        assert contact.pk == self.contact.pk

    def test_get_other_users_contact_raises_404(self):
        other = UserFactory(email="alien@test.com")
        their_contact = ContactFactory(owner=other, created_by=other)

        with pytest.raises(Http404):
            self.service.get_contact(their_contact.public_id)
