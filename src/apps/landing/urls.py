"""
Landing page URL configuration.

These routes are public (no auth required).
Mounted at the root "/" in config/urls.py — must be LAST.

Route format matches legacy Next.js project exactly:
  /inscrever-{slug}/   (capture pages)
  /obrigado-{slug}/    (thank-you pages)
  /checkout-{slug}/    (checkout pages)
  /checkout/return/    (post-payment return — new, internal)
  /checkout/*          (Stripe API endpoints — internal)
  /suporte/            (support)
  /terms-of-service/   (legal)
  /privacy-policy/     (legal)
"""

from django.urls import path, re_path

from apps.landing import checkout_views, views

app_name = "landing"

urlpatterns = [
    # ── Capture pages ─────────────────────────────────────────────
    # Legacy format: /inscrever-wh-rc-v3/, /inscrever-bf-v1/, etc.
    re_path(
        r"^inscrever-(?P<campaign_slug>[\w-]+)/$",
        views.capture_page,
        name="capture",
    ),
    # ── Thank-you pages ───────────────────────────────────────────
    # Legacy format: /obrigado-wh-rc-v3/, /obrigado-us/, etc.
    re_path(
        r"^obrigado-(?P<campaign_slug>[\w-]+)/$",
        views.thank_you_page,
        name="thank_you",
    ),
    # ── Checkout API endpoints (JSON, internal) ───────────────────
    # These use /checkout/ prefix (with slash) — no conflict with
    # /checkout-{slug}/ (with hyphen) page routes.
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
    # ── Checkout page (Inertia) ───────────────────────────────────
    # Legacy format: /checkout-wh/, /checkout-bf/, /checkout-z10k/
    re_path(
        r"^checkout-(?P<campaign_slug>[\w-]+)/$",
        checkout_views.checkout_page,
        name="checkout",
    ),
    # ── Support page ──────────────────────────────────────────────
    path("suporte/", views.support_page, name="support"),
    # ── Legal pages (legacy format) ───────────────────────────────
    path("terms-of-service/", views.terms_page, name="terms"),
    path("privacy-policy/", views.privacy_page, name="privacy"),
    # ── Home page (last — catch-all for root "/") ─────────────────
    path("", views.home, name="home"),
]
