"""
Billing views using Inertia.js.

All Stripe / djstripe logic is delegated to BillingService.
Views handle HTTP dispatch, service calls, and Inertia rendering only.

Security:
- Checkout restricted to POST to prevent CSRF link attacks
- Stripe error details are not leaked to the user
- Portal endpoint restricted to POST
"""

import logging

import stripe
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.inertia import inertia_render, flash_success, flash_error

from .services import BillingService

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """Billing overview page."""
    billing_data = BillingService.get_billing_data(request.user)

    return inertia_render(request, "Billing/Index", billing_data)


@login_required
@require_POST
def checkout(request, price_id: str):
    """
    Create Stripe checkout session and redirect.

    Restricted to POST to prevent CSRF-via-link attacks.
    Stripe error messages are logged but not exposed to the user.
    """
    try:
        checkout_url = BillingService.create_checkout_session(
            user=request.user,
            price_id=price_id,
            success_url=request.build_absolute_uri("/app/billing/success/"),
            cancel_url=request.build_absolute_uri("/app/billing/cancel/"),
        )
        return redirect(checkout_url)

    except stripe.error.StripeError as e:
        logger.error("Stripe checkout error for user %s: %s", request.user.id, e)
        flash_error(request, "A payment error occurred. Please try again.")
        return redirect("billing:index")

    except Exception as e:
        logger.error("Unexpected checkout error for user %s: %s", request.user.id, e)
        flash_error(request, "An unexpected error occurred. Please try again.")
        return redirect("billing:index")


@login_required
def success(request):
    """Checkout success page."""
    flash_success(request, "Payment successful! Thank you for your subscription.")
    return inertia_render(request, "Billing/Success")


@login_required
def cancel(request):
    """Checkout cancelled page."""
    flash_error(request, "Payment was cancelled.")
    return redirect("billing:index")


@login_required
@require_POST
def portal(request):
    """
    Redirect to Stripe Customer Portal.

    Restricted to POST to prevent CSRF-via-link attacks.
    """
    try:
        portal_url = BillingService.create_portal_session(
            user=request.user,
            return_url=request.build_absolute_uri("/app/billing/"),
        )
        return redirect(portal_url)

    except ValueError as e:
        logger.warning("Billing portal ValueError for user %s: %s", request.user.id, e)
        flash_error(request, "Unable to access billing portal. Please try again.")
        return redirect("billing:index")

    except Exception as e:
        logger.error("Billing portal error for user %s: %s", request.user.id, e)
        flash_error(request, "An error occurred accessing the billing portal.")
        return redirect("billing:index")
