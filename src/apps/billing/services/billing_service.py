"""
Billing service for Stripe integration via djstripe.

Standalone service (does NOT inherit BaseService) since it wraps
djstripe models and the Stripe API rather than managing a single
Django model with standard CRUD.

All methods are classmethods — no instance state required.

Provides 3 payment flows matching the legacy FastAPI server:
1. Embedded Checkout Session (subscription or one-time)
2. Payment Element + Subscription (two-step: customer → subscription)
3. One-time PaymentIntent
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class LineItem:
    """A single line item for Stripe operations."""

    price: str
    quantity: int = 1


@dataclass
class CheckoutResult:
    """Result from creating a Checkout Session."""

    client_secret: str
    session_id: str


@dataclass
class CustomerResult:
    """Result from creating a Stripe Customer."""

    customer_id: str
    email: str
    phone: str | None = None
    name: str | None = None


@dataclass
class SubscriptionResult:
    """Result from creating a Stripe Subscription."""

    subscription_id: str
    client_secret: str
    secret_type: str  # "payment" or "setup"
    status: str


@dataclass
class PaymentIntentResult:
    """Result from creating a PaymentIntent."""

    payment_intent_id: str
    client_secret: str
    status: str


@dataclass
class SessionStatus:
    """Status of a Stripe session/subscription/payment intent."""

    id: str
    status: str
    object_type: str  # "checkout_session", "subscription", "payment_intent"
    customer_email: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class BillingService:
    """
    Service for billing operations backed by Stripe / djstripe.

    Responsibilities:
    - Retrieve billing data (customer, subscription, invoices)
    - Create Stripe Checkout sessions (hosted + embedded)
    - Create Stripe Customers for Payment Element flow
    - Create Stripe Subscriptions (incomplete, pending confirmation)
    - Create Stripe PaymentIntents for one-time payments
    - Create Stripe Customer Portal sessions
    - Check subscription status for delinquent detection
    """

    # ── Stripe Configuration ─────────────────────────────────────────

    @classmethod
    def get_stripe_api_key(cls) -> str:
        """Return the correct Stripe secret key and set it globally."""
        if settings.STRIPE_LIVE_MODE:
            key = settings.STRIPE_LIVE_SECRET_KEY
        else:
            key = settings.STRIPE_TEST_SECRET_KEY

        stripe.api_key = key
        return key

    @classmethod
    def get_publishable_key(cls) -> str:
        """Return the Stripe publishable key for frontend use."""
        if settings.STRIPE_LIVE_MODE:
            return settings.STRIPE_LIVE_PUBLIC_KEY
        return settings.STRIPE_TEST_PUBLIC_KEY

    # ── Read Operations ──────────────────────────────────────────────

    @classmethod
    def get_billing_data(cls, user: Any) -> dict[str, Any]:
        """Gather billing data for a user from djstripe models.

        Returns a dict with:
            subscription: serialised Subscription or None
            invoices:     list of serialised recent Invoices

        On any failure the method logs a warning and returns safe
        defaults so the view never crashes.
        """
        data: dict[str, Any] = {
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

    @classmethod
    def is_user_delinquent(cls, user: Any) -> bool:
        """Check if a user's subscription is delinquent.

        A user is delinquent if they have a djstripe Customer linked
        AND their most recent subscription status is 'past_due' or 'unpaid'.

        Users with no customer or no subscription are NOT delinquent
        (they may be on a free plan or haven't subscribed yet).
        """
        try:
            from djstripe.models import Customer, Subscription

            customer = Customer.objects.filter(subscriber=user).first()
            if not customer:
                return False

            latest_sub = (
                Subscription.objects.filter(customer=customer)
                .order_by("-created")
                .first()
            )
            if not latest_sub:
                return False

            return latest_sub.status in ("past_due", "unpaid")

        except Exception:
            logger.warning(
                "Failed to check delinquent status for user=%s",
                getattr(user, "pk", "unknown"),
                exc_info=True,
            )
            # Fail open — don't block users due to errors
            return False

    # ── Hosted Checkout (Dashboard — redirect-based) ─────────────────

    @classmethod
    def create_checkout_session(
        cls,
        user: Any,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a hosted Stripe Checkout Session for dashboard users.

        Returns the Checkout Session URL to redirect the user to.
        Used by the dashboard billing page (authenticated users).
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
            "Hosted checkout session created: user=%s price=%s session=%s",
            user.pk,
            price_id,
            session.id,
        )
        return session.url

    # ── Embedded Checkout (Landing — in-page) ────────────────────────

    @classmethod
    def create_embedded_checkout_session(
        cls,
        *,
        line_items: list[LineItem],
        mode: str = "subscription",
        return_url: str,
        billing_address_collection: str = "auto",
        phone_number_collection: bool = True,
        trial_period_days: int = 0,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutResult:
        """Create an embedded Stripe Checkout Session (landing pages).

        Returns the client_secret for Stripe.js embedded checkout.
        Unlike the hosted version, this renders inline on the page.

        Args:
            line_items: List of LineItem(price, quantity).
            mode: 'subscription', 'payment', or 'setup'.
            return_url: URL to redirect after completion. Must contain
                        {CHECKOUT_SESSION_ID} placeholder.
            billing_address_collection: 'auto' or 'required'.
            phone_number_collection: Whether to collect phone number.
            trial_period_days: Free trial days (subscription mode only).
            metadata: Arbitrary metadata to attach to the session.
            idempotency_key: Optional idempotency key for retries.
        """
        cls.get_stripe_api_key()

        if mode not in ("subscription", "payment", "setup"):
            raise ValueError(f"Invalid mode: {mode}")

        session_params: dict[str, Any] = {
            "ui_mode": "embedded",
            "line_items": [
                {"price": item.price, "quantity": item.quantity} for item in line_items
            ],
            "mode": mode,
            "return_url": return_url,
            "billing_address_collection": billing_address_collection,
            "automatic_tax": {"enabled": True},
            "phone_number_collection": {"enabled": phone_number_collection},
        }

        if mode == "subscription" and trial_period_days > 0:
            session_params["subscription_data"] = {
                "trial_period_days": trial_period_days,
            }

        if metadata:
            session_params["metadata"] = {k: str(v) for k, v in metadata.items()}

        kwargs: dict[str, Any] = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        session = stripe.checkout.Session.create(**session_params, **kwargs)

        logger.info(
            "Embedded checkout session created: mode=%s session=%s",
            mode,
            session.id,
        )
        return CheckoutResult(
            client_secret=session.client_secret,
            session_id=session.id,
        )

    # ── Customer Creation (Payment Element flow) ─────────────────────

    @classmethod
    def create_customer(
        cls,
        *,
        email: str,
        phone: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> CustomerResult:
        """Create a Stripe Customer.

        Used as step 1 of the Payment Element flow.
        The customer_id is then passed to create_subscription().
        """
        cls.get_stripe_api_key()

        params: dict[str, Any] = {"email": email}
        if phone:
            params["phone"] = phone
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = {k: str(v) for k, v in metadata.items()}

        kwargs: dict[str, Any] = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        customer = stripe.Customer.create(**params, **kwargs)

        logger.info(
            "Stripe customer created: customer=%s email=%s",
            customer.id,
            email,
        )
        return CustomerResult(
            customer_id=customer.id,
            email=customer.email or email,
            phone=customer.phone,
            name=customer.name,
        )

    # ── Subscription (Payment Element flow) ──────────────────────────

    @classmethod
    def create_subscription(
        cls,
        *,
        customer_id: str,
        line_items: list[LineItem],
        add_invoice_items: list[LineItem] | None = None,
        trial_period_days: int = 0,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> SubscriptionResult:
        """Create a Stripe Subscription via the Payment Element flow.

        The subscription starts as 'incomplete' and only activates
        when the frontend confirms payment via Stripe.js.

        Returns the client_secret for stripe.confirmPayment() or
        stripe.confirmSetup() depending on whether payment is needed.
        """
        cls.get_stripe_api_key()

        params: dict[str, Any] = {
            "customer": customer_id,
            "items": [
                {"price": item.price, "quantity": item.quantity} for item in line_items
            ],
            "payment_behavior": "default_incomplete",
            "payment_settings": {
                "save_default_payment_method": "on_subscription",
            },
            "expand": [
                "latest_invoice.confirmation_secret",
                "pending_setup_intent",
            ],
        }

        if add_invoice_items:
            params["add_invoice_items"] = [
                {"price": item.price, "quantity": item.quantity}
                for item in add_invoice_items
            ]

        if trial_period_days > 0:
            params["trial_period_days"] = trial_period_days

        if metadata:
            params["metadata"] = {k: str(v) for k, v in metadata.items()}
            params["metadata"]["source"] = "payment_element_subscription"

        kwargs: dict[str, Any] = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        subscription = stripe.Subscription.create(**params, **kwargs)

        # Determine client_secret and type
        client_secret = ""
        secret_type = "payment"

        if subscription.pending_setup_intent:
            # Trial or $0 — no payment needed, just setup
            client_secret = subscription.pending_setup_intent.client_secret
            secret_type = "setup"
        elif (
            subscription.latest_invoice
            and hasattr(subscription.latest_invoice, "confirmation_secret")
            and subscription.latest_invoice.confirmation_secret
        ):
            client_secret = (
                subscription.latest_invoice.confirmation_secret.client_secret
            )
            secret_type = "payment"

        logger.info(
            "Subscription created: customer=%s subscription=%s status=%s type=%s",
            customer_id,
            subscription.id,
            subscription.status,
            secret_type,
        )
        return SubscriptionResult(
            subscription_id=subscription.id,
            client_secret=client_secret,
            secret_type=secret_type,
            status=subscription.status,
        )

    # ── PaymentIntent (one-time payments) ────────────────────────────

    @classmethod
    def create_payment_intent(
        cls,
        *,
        line_items: list[LineItem],
        return_url: str,
        customer_email: str | None = None,
        currency: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> PaymentIntentResult:
        """Create a Stripe PaymentIntent for one-time payments.

        Calculates the total amount from the line items' Stripe Prices.
        """
        cls.get_stripe_api_key()

        # Resolve total amount from Stripe Price objects
        total_amount = 0
        resolved_currency = currency
        price_ids: list[str] = []

        for item in line_items:
            price = stripe.Price.retrieve(item.price)
            total_amount += price.unit_amount * item.quantity
            price_ids.append(item.price)
            if not resolved_currency:
                resolved_currency = price.currency

        if not resolved_currency:
            resolved_currency = "brl"

        params: dict[str, Any] = {
            "amount": total_amount,
            "currency": resolved_currency,
            "automatic_payment_methods": {"enabled": True},
        }

        if customer_email:
            params["receipt_email"] = customer_email

        pi_metadata: dict[str, str] = {
            "source": "payment_element",
            "price_ids": ",".join(price_ids),
            "return_url": return_url,
            "product_count": str(len(line_items)),
        }
        if metadata:
            pi_metadata.update({k: str(v) for k, v in metadata.items()})
        params["metadata"] = pi_metadata

        kwargs: dict[str, Any] = {}
        if idempotency_key:
            kwargs["idempotency_key"] = idempotency_key

        intent = stripe.PaymentIntent.create(**params, **kwargs)

        logger.info(
            "PaymentIntent created: intent=%s amount=%s %s",
            intent.id,
            total_amount,
            resolved_currency,
        )
        return PaymentIntentResult(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            status=intent.status,
        )

    # ── Status Retrieval ─────────────────────────────────────────────

    @classmethod
    def get_session_status(cls, session_id: str) -> SessionStatus:
        """Smart status retrieval — auto-detects object type from ID prefix.

        Supports:
        - cs_*  → Checkout Session
        - sub_* → Subscription
        - pi_*  → PaymentIntent
        """
        cls.get_stripe_api_key()

        if session_id.startswith("cs_"):
            session = stripe.checkout.Session.retrieve(session_id)
            return SessionStatus(
                id=session.id,
                status=session.status or "",
                object_type="checkout_session",
                customer_email=session.customer_details.email
                if session.customer_details
                else "",
                extra={"payment_status": session.payment_status},
            )
        elif session_id.startswith("sub_"):
            sub = stripe.Subscription.retrieve(session_id)
            return SessionStatus(
                id=sub.id,
                status=sub.status,
                object_type="subscription",
            )
        elif session_id.startswith("pi_"):
            intent = stripe.PaymentIntent.retrieve(session_id)
            return SessionStatus(
                id=intent.id,
                status=intent.status,
                object_type="payment_intent",
            )
        else:
            raise ValueError(f"Unknown session ID prefix: {session_id[:4]}")

    # ── Customer Portal ──────────────────────────────────────────────

    @classmethod
    def create_portal_session(cls, user: Any, return_url: str) -> str:
        """Create a Stripe Customer Portal session.

        Returns the portal session URL.
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
            "Portal session created: user=%s customer=%s",
            user.pk,
            customer.id,
        )
        return session.url
