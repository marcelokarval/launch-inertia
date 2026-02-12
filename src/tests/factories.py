"""
Model factories for tests.

Uses factory_boy to create test instances of all major models.
"""

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = "identity.User"
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    email_verified = True
    status = "active"
    setup_status = "complete"

    class Params:
        """Trait params for common variations."""

        unverified = factory.Trait(
            email_verified=False,
            status="pending",
        )
        incomplete_setup = factory.Trait(
            setup_status="incomplete",
        )
        staff = factory.Trait(
            is_staff=True,
        )
        superuser = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )
        locked = factory.Trait(
            status="locked",
            failed_login_attempts=5,
        )


class ProfileFactory(DjangoModelFactory):
    """Factory for creating Profile instances."""

    class Meta:
        model = "identity.Profile"

    user = factory.SubFactory(UserFactory)
    phone = factory.Faker("phone_number")
    bio = factory.Faker("sentence")
    agreed_to_terms = True


class IdentityFactory(DjangoModelFactory):
    """Factory for creating Identity instances."""

    class Meta:
        model = "contact_identity.Identity"

    status = "active"
    confidence_score = factory.Faker("pyfloat", min_value=0.0, max_value=1.0)
    display_name = factory.Faker("name")
    first_seen_source = "manual"


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances."""

    class Meta:
        model = "contacts.Tag"

    name = factory.Sequence(lambda n: f"Tag {n}")
    color = factory.Faker("hex_color")


class NotificationFactory(DjangoModelFactory):
    """Factory for creating Notification instances."""

    class Meta:
        model = "notifications.Notification"

    recipient = factory.SubFactory(UserFactory)
    notification_type = "info"
    title = factory.Faker("sentence", nb_words=4)
    body = factory.Faker("paragraph")
    is_read = False
