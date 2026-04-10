"""
Signal receivers for subscription webhook events.

Handles:
- customer.subscription.deleted: Subscription was cancelled/expired
- customer.subscription.updated: Subscription status changed (active, past_due, etc.)
"""

import logging

from django.dispatch import receiver
from djstripe.signals import WEBHOOK_SIGNALS

logger = logging.getLogger(__name__)


@receiver(WEBHOOK_SIGNALS["customer.subscription.deleted"])
def handle_subscription_deleted(sender, event, **kwargs):
    """
    Process a deleted (cancelled/expired) subscription.

    Creates a notification informing the user their subscription has ended.
    The DelinquentMiddleware will handle access restriction based on
    the User.is_delinquent property once billing integration is complete.
    """
    subscription = event.data.get("object", {})
    customer_id = subscription.get("customer")

    user = _get_user_from_customer(customer_id)
    if not user:
        logger.warning(
            "Subscription deleted but user not found: customer=%s", customer_id
        )
        return

    logger.info(
        "Subscription deleted: user=%s subscription=%s",
        user.public_id,
        subscription.get("id"),
    )

    _create_notification(
        user,
        notification_type="warning",
        title="Subscription Ended",
        body=(
            "Your subscription has been cancelled. "
            "You can resubscribe at any time from the billing page."
        ),
        action_url="/app/billing/",
    )


@receiver(WEBHOOK_SIGNALS["customer.subscription.updated"])
def handle_subscription_updated(sender, event, **kwargs):
    """
    Process a subscription status change.

    Notifies the user when their subscription enters a problematic state
    (past_due, unpaid) or when it recovers to active.
    """
    subscription = event.data.get("object", {})
    customer_id = subscription.get("customer")
    status = subscription.get("status", "")
    previous = event.data.get("previous_attributes", {})
    previous_status = previous.get("status")

    # Only act if status actually changed
    if not previous_status or previous_status == status:
        return

    user = _get_user_from_customer(customer_id)
    if not user:
        return

    logger.info(
        "Subscription status changed: user=%s %s -> %s",
        user.public_id,
        previous_status,
        status,
    )

    if status == "past_due":
        _create_notification(
            user,
            notification_type="warning",
            title="Payment Past Due",
            body=(
                "Your subscription payment is past due. "
                "Please update your payment method to avoid interruption."
            ),
        )
    elif status == "active" and previous_status in ("past_due", "unpaid", "incomplete"):
        _create_notification(
            user,
            notification_type="success",
            title="Subscription Restored",
            body="Your subscription is now active again. Thank you!",
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
    user,
    notification_type: str,
    title: str,
    body: str,
    action_url: str = "/app/billing/",
):
    """Create an in-app notification for subscription events."""
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
            "Failed to create subscription notification for user=%s",
            user.public_id,
        )
