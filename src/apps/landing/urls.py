"""
Landing page URL configuration.

These routes are public (no auth required).
Mounted at the root "/" in config/urls.py — must be LAST.
"""

from django.urls import path

from apps.landing import checkout_views, views

app_name = "landing"

urlpatterns = [
    # Capture pages
    path(
        "inscrever/<slug:campaign_slug>/",
        views.capture_page,
        name="capture",
    ),
    # Thank-you pages (placeholder — full implementation in Phase F)
    path(
        "obrigado/<slug:campaign_slug>/",
        views.thank_you_page,
        name="thank_you",
    ),
    # ── Checkout API endpoints (JSON) ─────────────────────────────
    # These MUST come before checkout/<slug> to avoid slug capture
    path(
        "checkout/return/",
        checkout_views.checkout_return,
        name="checkout_return",
    ),
    path(
        "checkout/create-session/",
        checkout_views.create_checkout_session,
        name="checkout_create_session",
    ),
    path(
        "checkout/create-customer/",
        checkout_views.create_customer,
        name="checkout_create_customer",
    ),
    path(
        "checkout/create-subscription/",
        checkout_views.create_subscription,
        name="checkout_create_subscription",
    ),
    path(
        "checkout/create-payment-intent/",
        checkout_views.create_payment_intent,
        name="checkout_create_payment_intent",
    ),
    path(
        "checkout/session-status/",
        checkout_views.session_status,
        name="checkout_session_status",
    ),
    # ── Checkout page (Inertia — slug capture, must be LAST) ─────
    path(
        "checkout/<slug:campaign_slug>/",
        checkout_views.checkout_page,
        name="checkout",
    ),
    # Home page (last — catch-all for root "/")
    path("", views.home, name="home"),
]
