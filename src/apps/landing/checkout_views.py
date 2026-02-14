"""
Landing checkout views.

JSON API endpoints for Stripe payment flows (no auth required).
These are NOT Inertia views — they return JsonResponse for Stripe.js SDK.

Plus two Inertia page views:
- checkout_page: renders Checkout/Index.tsx (embedded checkout UI)
- checkout_return: renders Checkout/Return.tsx (post-payment status)

All POST endpoints are CSRF-protected via Django middleware.
Frontend sends CSRF token via X-XSRF-TOKEN header (read from cookie).
"""

import json
import logging
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from apps.billing.services.billing_service import (
    BillingService,
    LineItem,
)
from apps.landing.campaigns import get_campaign, get_campaign_or_default
from core.inertia.helpers import inertia_render

logger = logging.getLogger(__name__)


def _parse_json_body(request: HttpRequest) -> dict[str, Any]:
    """Parse JSON body from request.

    Uses request.data if available (set by InertiaJsonParserMiddleware),
    otherwise falls back to parsing request.body directly.
    """
    data = getattr(request, "data", None)
    if data is not None:
        return data

    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _parse_line_items(raw_items: list[dict[str, Any]]) -> list[LineItem]:
    """Convert raw dicts to LineItem dataclasses.

    Args:
        raw_items: List of dicts with 'price' (str) and optional 'quantity' (int).

    Returns:
        List of LineItem instances.

    Raises:
        ValueError: If any item is missing 'price' or has invalid format.
    """
    items: list[LineItem] = []
    for item in raw_items:
        price = item.get("price")
        if not price or not isinstance(price, str):
            raise ValueError("Each line item must have a 'price' string")
        quantity = item.get("quantity", 1)
        if not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Quantity must be a positive integer")
        items.append(LineItem(price=price, quantity=quantity))
    return items


def _error_response(message: str, status: int = 400) -> JsonResponse:
    """Return a standardized error JSON response."""
    return JsonResponse({"error": message}, status=status)


# ── Inertia Page Views ────────────────────────────────────────────────


@require_GET
def checkout_page(request: HttpRequest, campaign_slug: str) -> HttpResponse:
    """Render the embedded Checkout page.

    URL: /checkout-<campaign_slug>/

    Passes campaign checkout config + Stripe publishable key as props
    so the frontend can initialize Stripe.js and create a session.

    Fallback: non-existent slugs redirect to home.
    """
    campaign = get_campaign(campaign_slug)
    if campaign is None:
        from django.shortcuts import redirect

        return redirect("/")
    checkout_config = campaign.get("checkout", {})

    props: dict[str, Any] = {
        "campaign_slug": campaign_slug,
        "stripe_publishable_key": BillingService.get_publishable_key(),
        "checkout_config": {
            "mode": checkout_config.get("mode", "subscription"),
            "line_items": checkout_config.get("line_items", []),
            "trial_period_days": checkout_config.get("trial_period_days", 0),
            "phone_number_collection": checkout_config.get(
                "phone_number_collection", True
            ),
            "billing_address_collection": checkout_config.get(
                "billing_address_collection", "auto"
            ),
        },
        "campaign_meta": campaign.get("meta", {}),
    }

    return inertia_render(request, "Checkout/Index", props, app="landing")


@require_GET
def checkout_return(request: HttpRequest) -> HttpResponse:
    """Render the post-payment return page.

    URL: /checkout/return/

    The session_id is in the URL query params (injected by Stripe).
    Frontend reads it and calls GET /checkout/session-status/ to check.
    """
    session_id = request.GET.get("session_id", "")

    props: dict[str, Any] = {
        "session_id": session_id,
        "stripe_publishable_key": BillingService.get_publishable_key(),
    }

    return inertia_render(request, "Checkout/Return", props, app="landing")


# ── JSON API Endpoints ────────────────────────────────────────────────


@require_POST
def create_checkout_session(request: HttpRequest) -> JsonResponse:
    """Create an embedded Stripe Checkout Session.

    URL: POST /checkout/create-session/

    Request body (JSON):
        line_items: [{price: "price_xxx", quantity: 1}, ...]
        mode: "subscription" | "payment" | "setup"  (default: "subscription")
        return_url: str  (must contain {CHECKOUT_SESSION_ID})
        trial_period_days: int  (optional, default: 0)
        phone_number_collection: bool  (optional, default: true)
        billing_address_collection: "auto" | "required"  (optional)
        metadata: dict  (optional)
        idempotency_key: str  (optional)

    Returns:
        {clientSecret: str, sessionId: str}
    """
    data = _parse_json_body(request)

    raw_items = data.get("line_items")
    if not raw_items or not isinstance(raw_items, list):
        return _error_response("line_items is required and must be a list")

    return_url = data.get("return_url")
    if not return_url or not isinstance(return_url, str):
        return _error_response("return_url is required")

    try:
        line_items = _parse_line_items(raw_items)
    except ValueError as e:
        return _error_response(str(e))

    mode = data.get("mode", "subscription")
    if mode not in ("subscription", "payment", "setup"):
        return _error_response("mode must be 'subscription', 'payment', or 'setup'")

    try:
        result = BillingService.create_embedded_checkout_session(
            line_items=line_items,
            mode=mode,
            return_url=return_url,
            trial_period_days=data.get("trial_period_days", 0),
            phone_number_collection=data.get("phone_number_collection", True),
            billing_address_collection=data.get("billing_address_collection", "auto"),
            metadata=data.get("metadata"),
            idempotency_key=data.get("idempotency_key"),
        )
    except ValueError as e:
        return _error_response(str(e))
    except Exception:
        logger.exception("Failed to create checkout session")
        return _error_response("Failed to create checkout session", status=500)

    return JsonResponse(
        {
            "clientSecret": result.client_secret,
            "sessionId": result.session_id,
        }
    )


@require_POST
def create_customer(request: HttpRequest) -> JsonResponse:
    """Create a Stripe Customer (Payment Element flow, step 1).

    URL: POST /checkout/create-customer/

    Request body (JSON):
        email: str  (required)
        phone: str  (optional)
        name: str  (optional)
        metadata: dict  (optional)
        idempotency_key: str  (optional)

    Returns:
        {customerId: str, email: str, phone: str|null, name: str|null}
    """
    data = _parse_json_body(request)

    email = (data.get("email") or "").strip().lower()
    if not email:
        return _error_response("email is required")

    try:
        result = BillingService.create_customer(
            email=email,
            phone=data.get("phone"),
            name=data.get("name"),
            metadata=data.get("metadata"),
            idempotency_key=data.get("idempotency_key"),
        )
    except Exception:
        logger.exception("Failed to create Stripe customer")
        return _error_response("Failed to create customer", status=500)

    return JsonResponse(
        {
            "customerId": result.customer_id,
            "email": result.email,
            "phone": result.phone,
            "name": result.name,
        }
    )


@require_POST
def create_subscription(request: HttpRequest) -> JsonResponse:
    """Create a Stripe Subscription (Payment Element flow, step 2).

    URL: POST /checkout/create-subscription/

    Request body (JSON):
        customer_id: str  (required — from create_customer)
        line_items: [{price: "price_xxx", quantity: 1}, ...]  (required)
        add_invoice_items: [{price: "price_xxx", quantity: 1}, ...]  (optional)
        trial_period_days: int  (optional, default: 0)
        metadata: dict  (optional)
        idempotency_key: str  (optional)

    Returns:
        {subscriptionId: str, clientSecret: str, secretType: "payment"|"setup", status: str}
    """
    data = _parse_json_body(request)

    customer_id = data.get("customer_id")
    if not customer_id or not isinstance(customer_id, str):
        return _error_response("customer_id is required")

    raw_items = data.get("line_items")
    if not raw_items or not isinstance(raw_items, list):
        return _error_response("line_items is required and must be a list")

    try:
        line_items = _parse_line_items(raw_items)
    except ValueError as e:
        return _error_response(str(e))

    add_invoice_items = None
    raw_add_items = data.get("add_invoice_items")
    if raw_add_items:
        try:
            add_invoice_items = _parse_line_items(raw_add_items)
        except ValueError as e:
            return _error_response(f"add_invoice_items: {e}")

    try:
        result = BillingService.create_subscription(
            customer_id=customer_id,
            line_items=line_items,
            add_invoice_items=add_invoice_items,
            trial_period_days=data.get("trial_period_days", 0),
            metadata=data.get("metadata"),
            idempotency_key=data.get("idempotency_key"),
        )
    except Exception:
        logger.exception("Failed to create subscription")
        return _error_response("Failed to create subscription", status=500)

    return JsonResponse(
        {
            "subscriptionId": result.subscription_id,
            "clientSecret": result.client_secret,
            "secretType": result.secret_type,
            "status": result.status,
        }
    )


@require_POST
def create_payment_intent(request: HttpRequest) -> JsonResponse:
    """Create a Stripe PaymentIntent for one-time payments.

    URL: POST /checkout/create-payment-intent/

    Request body (JSON):
        line_items: [{price: "price_xxx", quantity: 1}, ...]  (required)
        return_url: str  (required)
        customer_email: str  (optional — for receipt)
        currency: str  (optional, default: resolved from Price)
        metadata: dict  (optional)
        idempotency_key: str  (optional)

    Returns:
        {paymentIntentId: str, clientSecret: str, status: str}
    """
    data = _parse_json_body(request)

    raw_items = data.get("line_items")
    if not raw_items or not isinstance(raw_items, list):
        return _error_response("line_items is required and must be a list")

    return_url = data.get("return_url")
    if not return_url or not isinstance(return_url, str):
        return _error_response("return_url is required")

    try:
        line_items = _parse_line_items(raw_items)
    except ValueError as e:
        return _error_response(str(e))

    try:
        result = BillingService.create_payment_intent(
            line_items=line_items,
            return_url=return_url,
            customer_email=data.get("customer_email"),
            currency=data.get("currency"),
            metadata=data.get("metadata"),
            idempotency_key=data.get("idempotency_key"),
        )
    except Exception:
        logger.exception("Failed to create payment intent")
        return _error_response("Failed to create payment intent", status=500)

    return JsonResponse(
        {
            "paymentIntentId": result.payment_intent_id,
            "clientSecret": result.client_secret,
            "status": result.status,
        }
    )


@require_GET
def session_status(request: HttpRequest) -> JsonResponse:
    """Get the status of a Stripe session/subscription/payment intent.

    URL: GET /checkout/session-status/?session_id=<id>

    Smart routing based on ID prefix:
    - cs_*  → Checkout Session
    - sub_* → Subscription
    - pi_*  → PaymentIntent

    Returns:
        {id: str, status: str, objectType: str, customerEmail: str, extra: dict}
    """
    session_id = request.GET.get("session_id", "")
    if not session_id:
        return _error_response("session_id query parameter is required")

    try:
        result = BillingService.get_session_status(session_id)
    except ValueError as e:
        return _error_response(str(e))
    except Exception:
        logger.exception("Failed to retrieve session status: %s", session_id)
        return _error_response("Failed to retrieve session status", status=500)

    return JsonResponse(
        {
            "id": result.id,
            "status": result.status,
            "objectType": result.object_type,
            "customerEmail": result.customer_email,
            "extra": result.extra,
        }
    )
