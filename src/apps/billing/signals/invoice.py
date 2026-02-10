"""
Signal receivers for invoice webhook events.

Handles:
- invoice.paid: Subscription payment succeeded
- invoice.payment_failed: Subscription payment failed (may trigger delinquent state)
"""

import logging

from django.dispatch import receiver
from djstripe.signals import WEBHOOK_SIGNALS

logger = logging.getLogger(__name__)


@receiver(WEBHOOK_SIGNALS["invoice.paid"])
def handle_invoice_paid(sender, event, **kwargs):
    """
    Process a paid invoice.

    djstripe has already synced the Invoice object.
    We create a success notification for the user.
    """
    invoice = event.data.get("object", {})
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_paid", 0)
    currency = invoice.get("currency", "usd").upper()

    user = _get_user_from_customer(customer_id)
    if not user:
        logger.warning("Invoice paid but user not found: customer=%s", customer_id)
        return

    # Format amount (Stripe amounts are in cents)
    formatted_amount = f"{currency} {amount / 100:.2f}"

    logger.info(
        "Invoice paid: user=%s amount=%s",
        user.public_id,
        formatted_amount,
    )

    _create_notification(
        user,
        notification_type="success",
        title="Payment Received",
        body=f"Your payment of {formatted_amount} was processed successfully.",
    )


@receiver(WEBHOOK_SIGNALS["invoice.payment_failed"])
def handle_invoice_payment_failed(sender, event, **kwargs):
    """
    Process a failed invoice payment.

    Creates a warning notification and logs the failure.
    The delinquent middleware will handle restricting access
    if the subscription enters past_due/unpaid status.
    """
    invoice = event.data.get("object", {})
    customer_id = invoice.get("customer")
    attempt_count = invoice.get("attempt_count", 0)

    user = _get_user_from_customer(customer_id)
    if not user:
        logger.warning(
            "Invoice payment failed but user not found: customer=%s", customer_id
        )
        return

    logger.warning(
        "Invoice payment failed: user=%s attempt=%d",
        user.public_id,
        attempt_count,
    )

    _create_notification(
        user,
        notification_type="warning",
        title="Payment Failed",
        body=(
            "We were unable to process your payment. "
            "Please update your billing information to avoid service interruption."
        ),
        action_url="/billing/",
    )


def _get_user_from_customer(stripe_customer_id: str):
    """Look up User from a Stripe customer ID via djstripe."""
    if not stripe_customer_id:
        return None

    try:
        from djstripe.models import Customer

        customer = Customer.objects.filter(id=stripe_customer_id).first()
        if customer and customer.subscriber:
            return customer.subscriber
    except Exception:
        logger.exception("Failed to resolve user from customer=%s", stripe_customer_id)

    return None


def _create_notification(
    user, notification_type: str, title: str, body: str, action_url: str = "/billing/"
):
    """Create an in-app notification for billing events."""
    try:
        from apps.notifications.models import Notification

        Notification.objects.create(
            recipient=user,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
        )
    except Exception:
        logger.exception(
            "Failed to create billing notification for user=%s", user.public_id
        )
