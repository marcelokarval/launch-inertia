"""
Signal receiver for checkout.session.completed webhook events.

When a checkout session completes, we:
1. Link the Stripe Customer to our User (via djstripe)
2. Update the user's setup_status if they were on the onboarding plan selection step
3. Create a notification for the user
"""

import logging

from django.dispatch import receiver
from djstripe.signals import WEBHOOK_SIGNALS

from apps.identity.models import User

logger = logging.getLogger(__name__)


@receiver(WEBHOOK_SIGNALS["checkout.session.completed"])
def handle_checkout_session_completed(sender, event, **kwargs):
    """
    Process a completed checkout session.

    djstripe has already synced the Customer, Subscription, and Invoice
    objects by the time this receiver runs.
    """
    session = event.data.get("object", {})
    customer_email = session.get("customer_email", "")
    user_public_id = session.get("metadata", {}).get("user_id", "")
    subscription_id = session.get("subscription")

    logger.info(
        "Checkout completed: customer_email=%s user_id=%s subscription=%s",
        customer_email,
        user_public_id,
        subscription_id,
    )

    # Find the user
    user = _resolve_user(user_public_id, customer_email)
    if not user:
        logger.warning(
            "Checkout completed but user not found: user_id=%s email=%s",
            user_public_id,
            customer_email,
        )
        return

    # Link djstripe Customer to our User if not already linked
    _link_stripe_customer(user, session.get("customer"))

    # Complete onboarding plan selection if still in onboarding
    if user.setup_status != User.SetupStatus.COMPLETE:
        from apps.identity.services import SetupStatusService

        SetupStatusService.complete_plan_selection(user, plan="premium")
        logger.info("Onboarding plan step completed for user=%s", user.public_id)

    # Create notification
    _create_payment_notification(
        user,
        title="Payment Confirmed",
        body="Your subscription is now active. Thank you for your purchase!",
    )


def _resolve_user(public_id: str, email: str):
    """Try to find user by public_id first, then by email."""
    if public_id:
        try:
            return User.objects.get(public_id=public_id)
        except User.DoesNotExist:
            pass

    if email:
        try:
            return User.objects.get(email=email.lower().strip())
        except User.DoesNotExist:
            pass

    return None


def _link_stripe_customer(user, stripe_customer_id: str):
    """Link a Stripe Customer to our User via djstripe."""
    if not stripe_customer_id:
        return

    try:
        from djstripe.models import Customer

        customer, _ = Customer.objects.get_or_create(id=stripe_customer_id)
        if customer.subscriber != user:
            customer.subscriber = user
            customer.save(update_fields=["subscriber"])
            logger.info(
                "Linked Stripe customer %s to user %s",
                stripe_customer_id,
                user.public_id,
            )
    except Exception:
        logger.exception(
            "Failed to link Stripe customer %s to user %s",
            stripe_customer_id,
            user.public_id,
        )


def _create_payment_notification(user, title: str, body: str):
    """Create an in-app notification for a payment event."""
    try:
        from apps.notifications.models import Notification

        Notification.objects.create(
            recipient=user,
            notification_type="success",
            title=title,
            body=body,
            action_url="/app/billing/",
        )
    except Exception:
        logger.exception(
            "Failed to create payment notification for user=%s", user.public_id
        )
