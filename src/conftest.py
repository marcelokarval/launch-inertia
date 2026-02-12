"""
Root conftest.py for pytest.

Provides shared fixtures used across all test modules.
"""

import pytest
from django.test import RequestFactory

from tests.factories import (
    UserFactory,
    ProfileFactory,
    IdentityFactory,
    NotificationFactory,
)


# ── User Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def user(db):
    """A standard verified user with complete setup."""
    return UserFactory()


@pytest.fixture
def user_with_profile(db):
    """A user with an associated profile."""
    u = UserFactory()
    ProfileFactory(user=u)
    return u


@pytest.fixture
def other_user(db):
    """A second user (for ownership/IDOR tests)."""
    return UserFactory(email="other@test.com")


@pytest.fixture
def staff_user(db):
    """A staff user."""
    return UserFactory(email="staff@test.com", staff=True)


@pytest.fixture
def superuser(db):
    """A superuser."""
    return UserFactory(email="admin@test.com", superuser=True)


@pytest.fixture
def unverified_user(db):
    """A user with unverified email."""
    return UserFactory(email="unverified@test.com", unverified=True)


@pytest.fixture
def locked_user(db):
    """A user with a locked account."""
    return UserFactory(email="locked@test.com", locked=True)


# ── Request Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def rf():
    """Django RequestFactory instance."""
    return RequestFactory()


@pytest.fixture
def authenticated_request(rf, user):
    """A GET request with an authenticated user."""
    request = rf.get("/")
    request.user = user
    request.session = {}
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    return request


# ── Identity Fixtures ────────────────────────────────────────────────


@pytest.fixture
def identity(db):
    """A single active Identity."""
    from tests.factories import IdentityFactory

    return IdentityFactory()


@pytest.fixture
def identities(db):
    """A list of 3 active Identities."""
    from tests.factories import IdentityFactory

    return [IdentityFactory() for _ in range(3)]


# ── Notification Fixtures ────────────────────────────────────────────


@pytest.fixture
def notification(db, user):
    """An unread notification for the default user."""
    return NotificationFactory(recipient=user)


@pytest.fixture
def read_notification(db, user):
    """A read notification for the default user."""
    n = NotificationFactory(recipient=user, is_read=True)
    from django.utils import timezone

    n.read_at = timezone.now()
    n.save()
    return n
