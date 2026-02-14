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
  /suporte-launch/     (support — launch variant)
  /terms-of-service/   (legal)
  /privacy-policy/     (legal)

Non-existent capture slugs redirect to /inscrever-wh-rc-v3/ (default).
Non-existent obrigado/checkout slugs redirect to / (home).
"""

from django.urls import path, re_path

from apps.landing import checkout_views, views

app_name = "landing"

urlpatterns = [
    # ── Capture pages ─────────────────────────────────────────────
    # Legacy format: /inscrever-wh-rc-v3/, /inscrever-bf-v1/, etc.
    # Non-existent slugs → redirect to /inscrever-wh-rc-v3/
    re_path(
        r"^inscrever-(?P<campaign_slug>[\w-]+)/$",
        views.capture_page,
        name="capture",
    ),
    # ── Thank-you pages ───────────────────────────────────────────
    # Legacy format: /obrigado-wh-rc-v3/, /obrigado-us/, etc.
    # Non-existent slugs → redirect to /
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
    # Non-existent slugs → redirect to /
    re_path(
        r"^checkout-(?P<campaign_slug>[\w-]+)/$",
        checkout_views.checkout_page,
        name="checkout",
    ),
    # ── Capture aliases (legacy routes without inscrever- prefix) ──
    # /insc-base/ and /lista-de-espera/ are capture pages in the legacy
    # that don't follow the inscrever-{slug} pattern.
    path(
        "insc-base/",
        views.capture_page,
        {"campaign_slug": "insc-base"},
        name="capture_insc_base",
    ),
    path(
        "lista-de-espera/",
        views.capture_page,
        {"campaign_slug": "lista-de-espera"},
        name="capture_lista_espera",
    ),
    # ── Support pages ─────────────────────────────────────────────
    path("suporte/", views.support_page, name="support"),
    path("suporte-launch/", views.support_launch_page, name="support_launch"),
    # ── Legal pages (legacy format) ───────────────────────────────
    path("terms-of-service/", views.terms_page, name="terms"),
    path("privacy-policy/", views.privacy_page, name="privacy"),
    # ── Placeholder routes (legacy parity) ────────────────────────
    # Complex pages not yet ported to Inertia. Redirect to home
    # so legacy URLs don't 404.
    path("lembrete-bf/", views.placeholder_redirect, name="lembrete_bf"),
    path("recado-importante/", views.placeholder_redirect, name="recado_importante"),
    path("onboarding/", views.placeholder_redirect, name="onboarding"),
    path("agrelliflix/", views.placeholder_redirect, name="agrelliflix"),
    path("agrelliflix-aula-1/", views.placeholder_redirect, name="agrelliflix_aula_1"),
    path("agrelliflix-aula-2/", views.placeholder_redirect, name="agrelliflix_aula_2"),
    path("agrelliflix-aula-3/", views.placeholder_redirect, name="agrelliflix_aula_3"),
    path("agrelliflix-aula-4/", views.placeholder_redirect, name="agrelliflix_aula_4"),
    # ── Home page (last — catch-all for root "/") ─────────────────
    # Legacy: redirects to /inscrever-wh-rc-v3/
    path("", views.home, name="home"),
]
