"""
Billing service for Stripe integration via djstripe.

Standalone service (does NOT inherit BaseService) since it wraps
djstripe models and the Stripe API rather than managing a single
Django model with standard CRUD.

All methods are classmethods — no instance state required.
"""

import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


class BillingService:
    """
    Service for billing operations backed by Stripe / djstripe.

    Responsibilities:
    - Retrieve billing data (customer, subscription, invoices)
    - Create Stripe Checkout sessions
    - Create Stripe Customer Portal sessions
    - Configure the Stripe API key based on Django settings
    """

    # ── Stripe Configuration ─────────────────────────────────────────

    @classmethod
    def get_stripe_api_key(cls) -> str:
        """
        Return the correct Stripe secret key based on settings and
        configure the global ``stripe.api_key``.

        Returns:
            The active Stripe secret key string.
        """
        if settings.STRIPE_LIVE_MODE:
            key = settings.STRIPE_LIVE_SECRET_KEY
        else:
            key = settings.STRIPE_TEST_SECRET_KEY

        stripe.api_key = key
        return key

    # ── Read Operations ──────────────────────────────────────────────

    @classmethod
    def get_billing_data(cls, user) -> dict:
        """
        Gather billing data for a user from djstripe models.

        Returns a dict with:
            subscription: serialised Subscription or None
            invoices:     list of serialised recent Invoices

        On any failure the method logs a warning and returns safe
        defaults so the view never crashes.
        """
        data: dict = {
            "subscription": None,
            "invoices": [],
        }

        try:
            from djstripe.models import Customer, Invoice, Subscription

            customer = Customer.objects.filter(subscriber=user).first()
            if not customer:
                return data

            subscription = Subscription.objects.filter(
                customer=customer,
                status__in=["active", "trialing", "past_due"],
            ).first()

            invoices = Invoice.objects.filter(customer=customer).order_by("-created")[
                :10
            ]

            data["subscription"] = subscription.to_dict() if subscription else None
            data["invoices"] = [inv.to_dict() for inv in invoices]

        except Exception:
            logger.warning(
                "Failed to retrieve billing data for user=%s",
                user.pk,
                exc_info=True,
            )

        return data

    # ── Checkout ─────────────────────────────────────────────────────

    @classmethod
    def create_checkout_session(
        cls,
        user,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Create a Stripe Checkout Session for a subscription.

        Args:
            user:        The authenticated user initiating checkout.
            price_id:    The Stripe Price ID to subscribe to.
            success_url: Absolute URL to redirect on success.
            cancel_url:  Absolute URL to redirect on cancellation.

        Returns:
            The Checkout Session URL to redirect the user to.

        Raises:
            stripe.error.StripeError: On Stripe API failures.
        """
        cls.get_stripe_api_key()

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.email,
            metadata={"user_id": str(user.public_id)},
        )

        logger.info(
            "Checkout session created for user=%s price=%s session=%s",
            user.pk,
            price_id,
            session.id,
        )
        return session.url

    # ── Customer Portal ──────────────────────────────────────────────

    @classmethod
    def create_portal_session(cls, user, return_url: str) -> str:
        """
        Create a Stripe Customer Portal session.

        Args:
            user:       The authenticated user.
            return_url: Absolute URL to return to after the portal.

        Returns:
            The portal session URL.

        Raises:
            ValueError:             If no djstripe Customer exists for the user.
            stripe.error.StripeError: On Stripe API failures.
        """
        cls.get_stripe_api_key()

        from djstripe.models import Customer

        customer = Customer.objects.filter(subscriber=user).first()
        if not customer:
            raise ValueError("No billing account found for this user.")

        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=return_url,
        )

        logger.info(
            "Portal session created for user=%s customer=%s",
            user.pk,
            customer.id,
        )
        return session.url
