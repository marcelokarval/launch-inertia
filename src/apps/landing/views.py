"""
Landing page views.

Capture views handle both GET (render landing page) and POST (process form).
All landing views use app="landing" for the landing.html Inertia template.

Config resolution order (DB first, JSON fallback):
1. CapturePageService.get_page_config() — DB with Redis caching
2. get_campaign() — static JSON files (migration-period fallback)
3. get_campaign_or_default() — hardcoded defaults (safety net)
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.inertia.helpers import inertia_render
from core.shared.hashing import hash_email, hash_phone
from core.tracking.models import CaptureEvent
from core.tracking.services import TrackingService
from core.types import SameSiteType

from apps.ads.models import CaptureSubmission
from apps.ads.services.utm_parser import UTMParserService  # compatibility for tests
from apps.landing.campaigns import get_campaign, get_campaign_or_default
from apps.landing.services.capture import CaptureService
from apps.landing.services.page_config import LandingPageConfigService
from apps.launches.services import CapturePageService

logger = logging.getLogger(__name__)

# Default campaign slug — used as fallback for non-existent slugs.
DEFAULT_CAMPAIGN_SLUG = "wh-rc-v3"


def _legacy_json_fallback_enabled() -> bool:
    """Whether runtime JSON campaign fallback is currently allowed."""
    return bool(getattr(settings, "LANDING_JSON_FALLBACK_ENABLED", True))


def _track_redirect(request: HttpRequest, page_path: str) -> None:
    """Track a lightweight page_view event for redirect-only routes.

    Used for home, placeholder redirects, and other non-content routes.
    These events record that the visitor accessed the URL (journey attribution)
    but may not have full device/geo data if VisitorMiddleware was skipped.
    """
    try:
        capture_token = TrackingService.generate_capture_token()
        TrackingService.create_event(
            event_type=CaptureEvent.EventType.PAGE_VIEW,
            capture_token=capture_token,
            page_path=page_path,
            page_category=CaptureEvent.PageCategory.OTHER,
            request=request,
        )
    except Exception:
        # Tracking failure must never block a redirect
        logger.debug("Failed to track redirect for %s", page_path)


def _track_page_view(
    request: HttpRequest,
    page_path: str,
    page_category: CaptureEvent.PageCategory,
) -> None:
    """Track page_view event for config-driven landing pages.

    Extracts the repeated tracking pattern from views into a helper.
    Creates a capture token and fires a PAGE_VIEW event with the given
    path and category.

    Args:
        request: The incoming HTTP request.
        page_path: URL path for the event (e.g., "/lembrete-bf/").
        page_category: CaptureEvent.PageCategory enum value.
    """
    capture_token = TrackingService.generate_capture_token()
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path=page_path,
        page_category=page_category,
        request=request,
    )


def _set_hashed_pii_cookies(
    response: HttpResponse,
    email: str,
    phone: str,
) -> None:
    """Set hashed PII cookies (_em, _ph) on successful form submission.

    These cookies enable:
    - Returning-visitor identification (identity_middleware reads them)
    - Meta CAPI user_data matching (hashed email/phone for server events)

    Cookies are SHA-256 hashes (not raw PII), httponly=True (server-only),
    365-day lifetime matching Meta's attribution window.
    """
    from django.conf import settings

    secure: bool = getattr(settings, "SESSION_COOKIE_SECURE", False)
    samesite = cast(SameSiteType, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax"))
    max_age = 365 * 24 * 60 * 60  # 365 days

    if email:
        try:
            response.set_cookie(
                "_em",
                hash_email(email),
                max_age=max_age,
                httponly=True,
                secure=secure,
                samesite=samesite,
                path="/",
            )
        except ValueError:
            pass  # Empty email after normalization — skip

    if phone:
        try:
            response.set_cookie(
                "_ph",
                hash_phone(phone),
                max_age=max_age,
                httponly=True,
                secure=secure,
                samesite=samesite,
                path="/",
            )
        except ValueError:
            pass  # No digits in phone — skip


def _resolve_campaign_config(
    slug: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, Any]:
    """Resolve campaign config: DB first, then JSON fallback.

    Returns:
        Tuple of (frontend_props, backend_config, capture_page_model).
        - frontend_props: For Inertia rendering (no n8n keys).
        - backend_config: For POST handling (includes n8n, thank_you, etc.).
        - capture_page_model: CapturePage instance or None.
        All None if slug not found anywhere.
    """
    # Try DB first (CapturePageService) — single model fetch
    page = CapturePageService.get_page(slug)
    if page is not None:
        frontend_props = CapturePageService.get_page_config(slug)
        backend_config = CapturePageService.get_full_config(slug)
        return frontend_props, backend_config, page

    # Fallback to JSON files (migration period, non-production by default)
    if _legacy_json_fallback_enabled():
        json_config = get_campaign(slug)
        if json_config is not None:
            return json_config, json_config, None

    return None, None, None


def home(request: HttpRequest) -> HttpResponse:
    """Landing home page — redirects to default capture page.

    URL: /
    Legacy parity: root page redirects to /inscrever-wh-rc-v3/.
    Tracks page_view for visitor journey attribution.
    """
    _track_redirect(request, "/")
    return redirect(f"/inscrever-{DEFAULT_CAMPAIGN_SLUG}/")


def capture_page(request: HttpRequest, campaign_slug: str) -> HttpResponse:
    """Capture landing page — GET renders form, POST processes lead.

    URL: /inscrever-<campaign_slug>/

    GET: Serves the landing page with campaign config as Inertia props.
         Generates capture_token, creates page_view event, starts session.
    POST: Validates form, creates form_attempt/success/error events,
          resolves identity, forwards to N8N, redirects.

    Config resolution: DB (CapturePageService) → JSON fallback → defaults.
    Fallback: non-existent slugs redirect to /inscrever-wh-rc-v3/.
    """
    frontend_props, backend_config, capture_page_model = _resolve_campaign_config(
        campaign_slug
    )

    # Fallback: redirect to default campaign if slug doesn't exist
    if frontend_props is None:
        if campaign_slug != DEFAULT_CAMPAIGN_SLUG:
            return redirect(f"/inscrever-{DEFAULT_CAMPAIGN_SLUG}/")
        # Safety: if even the default doesn't exist, use generated defaults
        if _legacy_json_fallback_enabled():
            default_config = get_campaign_or_default(campaign_slug)
            frontend_props = default_config
            backend_config = default_config
        else:
            return HttpResponse("Capture page not configured.", status=404)

    if request.method == "POST":
        return _handle_capture_post(
            request,
            frontend_props,
            backend_config or frontend_props,
            campaign_slug,
            capture_page_model=capture_page_model,
        )

    # ── GET: generate capture_token, page_view event, start session ──
    capture_token = TrackingService.generate_capture_token()
    page_path = f"/inscrever-{campaign_slug}/"

    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path=page_path,
        page_category=CaptureEvent.PageCategory.CAPTURE,
        request=request,
        capture_page=capture_page_model,
    )

    TrackingService.start_capture_session(
        capture_token=capture_token,
        slug=campaign_slug,
        request=request,
    )

    # Pass session identity public_id to frontend (for JS correlation)
    identity_public_id = getattr(request, "identity_public_id", "")

    return _render_capture_page(
        request,
        frontend_props,
        campaign_slug,
        capture_token=capture_token,
        capture_page_public_id=getattr(capture_page_model, "public_id", ""),
        identity_public_id=identity_public_id,
    )


def _build_campaign_props(
    campaign: dict[str, Any], campaign_slug: str
) -> dict[str, Any]:
    """Build the campaign props dict for the Capture page.

    Includes all visual-parity fields (background_image, highlight_color,
    subheadline, button_gradient) used by the dark-theme landing frontend.

    When config comes from CapturePageService.get_page_config(), the dict
    already has the correct shape (to_props()). For JSON fallback, we
    extract the same keys.
    """
    props: dict[str, Any] = {
        "slug": campaign.get("slug", campaign_slug),
        "meta": campaign.get("meta", {}),
        "headline": campaign.get("headline", {}),
        "badges": campaign.get("badges", []),
        "form": campaign.get("form", {}),
        "trust_badge": campaign.get("trust_badge", {}),
        "social_proof": campaign.get("social_proof", {}),
    }

    # Optional visual-parity fields — only include when present
    for field in ("subheadline", "background_image", "highlight_color", "topBanner"):
        value = campaign.get(field)
        if value is not None:
            props[field] = value

    # DB-sourced pages include page_type and layout_type
    for field in ("page_type", "layout_type"):
        value = campaign.get(field)
        if value is not None:
            props[field] = value

    return props


def _render_capture_page(
    request: HttpRequest,
    campaign: dict[str, Any],
    campaign_slug: str,
    *,
    capture_token: str = "",
    capture_page_public_id: str = "",
    identity_public_id: str = "",
    errors: dict[str, str] | None = None,
) -> HttpResponse:
    """Render the Capture/Index page with campaign props.

    When errors are provided (POST validation failure), re-renders the
    page with errors as props so the frontend can display them inline.
    The identity_public_id is the session-based Identity for JS correlation.

    Pre-fill logic (returning visitors):
    1. If session Identity has ContactEmail/ContactPhone → use those
    2. Fallback to session email_hint/phone_hint (from capture-intent beacon)
    """
    props: dict[str, Any] = {
        "campaign": _build_campaign_props(campaign, campaign_slug),
        "capture_token": capture_token,
    }

    if capture_page_public_id:
        props["capture_page_public_id"] = capture_page_public_id

    # Session-based identity: always available from first page load
    if identity_public_id:
        props["identity_id"] = identity_public_id

    if errors:
        props["errors"] = errors

    # Pre-fill for returning visitors
    prefill = _resolve_prefill(request)
    if prefill:
        props["prefill"] = prefill

    return inertia_render(request, "Capture/Index", props, app="landing")


def _resolve_prefill(request: HttpRequest) -> dict[str, str] | None:
    """Resolve pre-fill data for returning visitors.

    Priority:
    1. Session Identity's primary ContactEmail/ContactPhone
    2. Session hints from capture-intent beacon

    Returns None if no pre-fill data available.
    """
    prefill: dict[str, str] = {}

    # Try resolved identity first (has email/phone from previous conversion)
    identity = getattr(request, "identity", None)
    if identity is not None:
        try:
            # Get best email (verified first, then most recent)
            primary_email = (
                identity.email_contacts.filter(is_deleted=False)
                .order_by("-is_verified", "-created_at")
                .values_list("value", flat=True)
                .first()
            )
            if primary_email:
                prefill["email"] = primary_email

            # Get best phone (verified first, then most recent)
            primary_phone = (
                identity.phone_contacts.filter(is_deleted=False)
                .order_by("-is_verified", "-created_at")
                .values_list("value", flat=True)
                .first()
            )
            if primary_phone:
                prefill["phone"] = primary_phone
        except Exception:
            logger.debug("Failed to resolve prefill from identity", exc_info=True)

    # Fallback: session hints from capture-intent beacon
    if not prefill.get("email") and hasattr(request, "session"):
        hint_email = request.session.get("email_hint", "")
        if hint_email:
            prefill["email"] = hint_email

    if not prefill.get("phone") and hasattr(request, "session"):
        hint_phone = request.session.get("phone_hint", "")
        if hint_phone:
            prefill["phone"] = hint_phone

    return prefill if prefill else None


def _handle_capture_post(
    request: HttpRequest,
    frontend_props: dict[str, Any],
    backend_config: dict[str, Any],
    campaign_slug: str,
    *,
    capture_page_model: Any = None,
) -> HttpResponse:
    """Handle capture form POST submission.

    Uses request.data (parsed by InertiaJsonParserMiddleware).
    Creates tracking events: form_attempt (always), then form_success
    or form_error depending on validation result.
    Re-renders page with errors on validation failure,
    or redirects to thank-you URL on success.

    On valid submit, delegates the orchestration to CaptureService.complete_capture()
    so the DB-facing operations run through a single transactional service path.

    Args:
        frontend_props: Config for re-rendering on validation error.
        backend_config: Full config including n8n keys for POST processing.
        campaign_slug: URL slug for redirect fallback.
        capture_page_model: Optional CapturePage instance for FK on events.
    """
    t_start = time.monotonic()
    data = getattr(request, "data", request.POST)
    page_path = f"/inscrever-{campaign_slug}/"

    # Recover capture_token from form data (generated on GET)
    capture_token = (
        data.get("capture_token", "") or TrackingService.generate_capture_token()
    )

    # Track form attempt (before validation)
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.FORM_ATTEMPT,
        capture_token=capture_token,
        page_path=page_path,
        page_category=CaptureEvent.PageCategory.CAPTURE,
        request=request,
        capture_page=capture_page_model,
    )

    # Server-side validation
    errors = CaptureService.validate_form_data(data)
    if errors:
        # Track form error
        TrackingService.create_event(
            event_type=CaptureEvent.EventType.FORM_ERROR,
            capture_token=capture_token,
            page_path=page_path,
            page_category=CaptureEvent.PageCategory.CAPTURE,
            request=request,
            capture_page=capture_page_model,
            extra_data={"validation_errors": errors},
        )
        # Re-render with the same capture_token so the next attempt
        # stays linked to the same page load session
        return _render_capture_page(
            request,
            frontend_props,
            campaign_slug,
            capture_token=capture_token,
            capture_page_public_id=getattr(capture_page_model, "public_id", ""),
            identity_public_id=getattr(request, "identity_public_id", ""),
            errors=errors,
        )

    capture_page_public_id = (data.get("capture_page_public_id") or "").strip()
    if capture_page_model is None and capture_page_public_id:
        capture_page_model = CapturePageService.get_page(campaign_slug)

    # Materialize legacy JSON-backed campaigns so successful submits always
    # have a concrete CapturePage FK for CaptureSubmission.
    if capture_page_model is None:
        capture_page_model = CapturePageService.materialize_legacy_page(
            campaign_slug,
            backend_config,
        )

    result = CaptureService.complete_capture(
        request=request,
        data=data,
        backend_config=backend_config,
        campaign_slug=campaign_slug,
        capture_token=capture_token,
        capture_page_model=capture_page_model,
        t_start=t_start,
    )
    identity = result.get("identity")
    submission = result.get("submission")
    email = result.get("email", "")
    phone = result.get("phone", "")
    page_url = result.get("page_url", request.build_absolute_uri())

    # External integrations are now enqueued through LeadIntegrationOutbox
    # inside CaptureService.complete_capture(). The request path only redirects.

    # Redirect to thank-you page
    thank_you_url = result.get("thank_you_url") or backend_config.get("form", {}).get(
        "thank_you_url",
        backend_config.get("thank_you", {}).get(
            "url", f"/obrigado-{backend_config.get('slug', campaign_slug)}/"
        ),
    )
    response = redirect(thank_you_url)

    # Set hashed PII cookies for returning-visitor matching + Meta CAPI
    _set_hashed_pii_cookies(response, email, phone)

    return response


def _dispatch_meta_capi_lead(
    *,
    email: str,
    phone: str,
    capture_token: str,
    page_url: str,
    request: HttpRequest,
    identity_public_id: str = "",
) -> None:
    """Dispatch Meta CAPI Lead event via Celery task.

    Reads META_PIXEL_ID / META_CAPI_ACCESS_TOKEN from env. Silently
    skips if not configured (dev environments typically have no token).

    All heavy work (SDK call, HTTP to Meta) happens in the Celery worker.
    This function only hashes + enqueues — never blocks the redirect.
    """
    pixel_id = os.getenv("META_PIXEL_ID", "")
    access_token = os.getenv("META_CAPI_ACCESS_TOKEN", "")

    if not pixel_id or not access_token:
        return  # CAPI not configured — skip silently

    try:
        test_event_code = os.getenv("META_CAPI_TEST_EVENT_CODE", "")

        # Hash PII for Meta matching (already have hash_email/hash_phone imported)
        email_hash = ""
        phone_hash = ""
        if email:
            try:
                email_hash = hash_email(email)
            except ValueError:
                pass
        if phone:
            try:
                phone_hash = hash_phone(phone)
            except ValueError:
                pass

        # Extract Meta cookies (_fbc, _fbp) from request
        fbc = request.COOKIES.get("_fbc", "")
        fbp = request.COOKIES.get("_fbp", "")

        # Client info for matching quality
        client_ip = getattr(request, "client_ip", "") or ""
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        from infrastructure.integrations.tasks import send_meta_conversion

        send_meta_conversion.delay(
            pixel_id=pixel_id,
            access_token=access_token,
            test_event_code=test_event_code,
            event_name="Lead",
            email_hash=email_hash,
            phone_hash=phone_hash,
            event_id=capture_token,
            event_source_url=page_url,
            client_ip=client_ip,
            user_agent=user_agent,
            fbc=fbc,
            fbp=fbp,
            external_id=identity_public_id,
        )

        logger.debug(
            "MetaCAPI Lead dispatched: pixel=%s, event_id=%s",
            pixel_id,
            capture_token[:12],
        )
    except Exception:
        # CAPI dispatch failure must NEVER block the capture flow
        logger.debug("Failed to dispatch MetaCAPI Lead event", exc_info=True)


def _create_capture_submission(
    *,
    identity: Any,
    email_raw: str,
    phone_raw: str,
    capture_page: Any,
    utm_data: dict[str, str],
    extra_ad_params: dict[str, str],
    capture_token: str,
    visitor_id: str,
    request: HttpRequest,
    t_start: float,
) -> CaptureSubmission | None:
    """Compatibility wrapper around CaptureService.create_capture_submission()."""
    return CaptureService.create_capture_submission(
        identity=identity,
        email_raw=email_raw,
        phone_raw=phone_raw,
        capture_page=capture_page,
        utm_data=utm_data,
        extra_ad_params=extra_ad_params,
        capture_token=capture_token,
        visitor_id=visitor_id,
        request=request,
        t_start=t_start,
    )


# ── Support page configuration ────────────────────────────────────────
# Site-wide (not per-campaign). Chatwoot credentials and FAQ data.

_CHATWOOT_CONFIG: dict[str, str] = {
    "website_token": "7c97wiFhBxyidsXA6tXN5kJc",
    "base_url": "https://atend.arthuragrelli.com",
    "locale": "pt_BR",
    "header_title": "Suporte Arthur Agrelli",
    "header_subtitle": "Online",
    "business_hours": (
        "Suporte disponivel de Segunda a Sexta, das 9h as 18h (Horario de Brasilia)"
    ),
}

_FAQ_ITEMS: list[dict[str, str]] = [
    {
        "id": "1",
        "category": "Metodo iREI",
        "question": "O que e o Metodo iREI?",
        "answer": (
            "O Metodo iREI e um sistema completo de investimento imobiliario "
            "nos EUA que ensina como ganhar +$10 mil/mes repassando casas sem "
            "tirar dinheiro do seu bolso."
        ),
    },
    {
        "id": "2",
        "category": "Metodo iREI",
        "question": "Preciso ter dinheiro para comecar?",
        "answer": (
            "Nao! O diferencial do metodo e justamente permitir que voce "
            "comece sem investir seu proprio capital. Voce aprende tecnicas "
            "de wholesale (repasse) onde o lucro vem da intermediacao."
        ),
    },
    {
        "id": "3",
        "category": "Metodo iREI",
        "question": "Preciso morar nos EUA?",
        "answer": (
            "Nao necessariamente. O metodo pode ser aplicado remotamente do "
            "Brasil, mas tambem funciona para quem mora nos EUA. Temos alunos "
            "em ambas situacoes obtendo resultados."
        ),
    },
    {
        "id": "4",
        "category": "Pagamento",
        "question": "Quais formas de pagamento sao aceitas?",
        "answer": (
            "Aceitamos cartao de credito (com parcelamento em ate 12x), PIX, "
            "boleto bancario e pagamentos internacionais via PayPal e cartoes "
            "internacionais."
        ),
    },
    {
        "id": "5",
        "category": "Pagamento",
        "question": "Tem garantia de devolucao?",
        "answer": (
            "Sim! Oferecemos garantia incondicional de 7 dias. Se por qualquer "
            "motivo voce nao ficar satisfeito, devolvemos 100%% do seu "
            "investimento sem perguntas."
        ),
    },
    {
        "id": "6",
        "category": "Acesso",
        "question": "Como acesso o conteudo apos a compra?",
        "answer": (
            "Imediatamente apos a confirmacao do pagamento, voce recebe um "
            "e-mail com suas credenciais de acesso a area de membros. Todo "
            "conteudo fica disponivel 24/7 na nossa plataforma."
        ),
    },
    {
        "id": "7",
        "category": "Acesso",
        "question": "Por quanto tempo tenho acesso?",
        "answer": (
            "Seu acesso e valido por 1 ano completo a partir da inscricao. "
            "Ao final desse periodo, voce pode renovar com condicoes especiais "
            "para alunos."
        ),
    },
    {
        "id": "8",
        "category": "Suporte",
        "question": "Como funciona o suporte aos alunos?",
        "answer": (
            "Oferecemos suporte atraves deste chat, e-mail e nossa comunidade "
            "exclusiva. Alem disso, temos mentorias em grupo semanais onde voce "
            "pode tirar duvidas diretamente com nossa equipe."
        ),
    },
]

_FAQ_CATEGORIES: list[str] = ["Metodo iREI", "Pagamento", "Acesso", "Suporte"]


@require_GET
def support_page(request: HttpRequest) -> HttpResponse:
    """Support page with live chat and FAQ.

    URL: /suporte/

    Renders the Central de Suporte page with Chatwoot widget and FAQ panel.
    Config is site-wide (not campaign-specific).
    Tracks page_view event.
    """
    # Track page_view
    capture_token = TrackingService.generate_capture_token()
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path="/suporte/",
        page_category=CaptureEvent.PageCategory.SUPPORT,
        request=request,
    )

    return inertia_render(
        request,
        "Support/Index",
        {
            "support": {
                "chatwoot": _CHATWOOT_CONFIG,
                "faq_items": _FAQ_ITEMS,
                "faq_categories": _FAQ_CATEGORIES,
            },
        },
        app="landing",
    )


@require_GET
def terms_page(request: HttpRequest) -> HttpResponse:
    """Terms of Service page.

    URL: /terms-of-service/
    Tracks page_view event.
    """
    capture_token = TrackingService.generate_capture_token()
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path="/terms-of-service/",
        page_category=CaptureEvent.PageCategory.LEGAL,
        request=request,
    )
    return inertia_render(request, "Legal/Terms", {}, app="landing")


@require_GET
def privacy_page(request: HttpRequest) -> HttpResponse:
    """Privacy Policy page.

    URL: /privacy-policy/
    Tracks page_view event.
    """
    capture_token = TrackingService.generate_capture_token()
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path="/privacy-policy/",
        page_category=CaptureEvent.PageCategory.LEGAL,
        request=request,
    )
    return inertia_render(request, "Legal/Privacy", {}, app="landing")


@require_GET
def thank_you_page(request: HttpRequest, campaign_slug: str) -> HttpResponse:
    """Thank-you page after successful capture.

    URL: /obrigado-<campaign_slug>/

    Renders urgency-driven page with WhatsApp CTA, countdown timer,
    and progress bar. Config resolution: DB first, JSON fallback.
    Tracks page_view event.

    Fallback: non-existent slugs redirect to home.
    """
    # DB first, then JSON fallback
    _, backend_config, capture_page_model = _resolve_campaign_config(campaign_slug)

    if backend_config is None:
        return redirect("/")

    # Track page_view
    capture_token = TrackingService.generate_capture_token()
    page_path = f"/obrigado-{campaign_slug}/"
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.PAGE_VIEW,
        capture_token=capture_token,
        page_path=page_path,
        page_category=CaptureEvent.PageCategory.THANK_YOU,
        request=request,
        capture_page=capture_page_model,
    )

    campaign = backend_config
    thank_you_config = campaign.get("thank_you", {})

    # Build thank_you props with sensible defaults
    thank_you_props: dict[str, Any] = {
        "headline": thank_you_config.get("headline", "Inscricao confirmada!"),
        "subheadline": thank_you_config.get(
            "subheadline", "Falta apenas um passo para completar."
        ),
        "whatsapp_group_link": thank_you_config.get("whatsapp_group_link", ""),
        "whatsapp_button_text": thank_you_config.get(
            "whatsapp_button_text", "ENTRAR NO GRUPO VIP"
        ),
        "countdown_minutes": thank_you_config.get("countdown_minutes", 15),
        "show_social_proof": thank_you_config.get("show_social_proof", True),
        "social_proof_text": thank_you_config.get("social_proof_text", ""),
        "steps": thank_you_config.get(
            "steps",
            [
                {"label": "Cadastro", "completed": True},
                {"label": "Confirmacao", "completed": True},
                {"label": "Grupo VIP", "completed": False},
            ],
        ),
        "progress_percentage": thank_you_config.get("progress_percentage", 66),
    }

    return inertia_render(
        request,
        "ThankYou/Index",
        {
            "campaign": {
                "slug": campaign.get("slug", campaign_slug),
                "meta": campaign.get("meta", {}),
            },
            "thank_you": thank_you_props,
        },
        app="landing",
    )


# ── Fingerprint beacon endpoint ────────────────────────────────────────


@csrf_exempt
@require_POST
def fp_resolve(request: HttpRequest) -> HttpResponse:
    """Receive FingerprintJS Pro result via sendBeacon.

    URL: /api/fp-resolve/

    Called by the landing frontend immediately after FingerprintJS Pro
    resolves (~200ms after page load). Uses sendBeacon so the request
    completes even if the user bounces.

    Payload (JSON or form-encoded):
        visitor_id:     FingerprintJS visitorId (required)
        request_id:     FingerprintJS requestId
        confidence:     Confidence score (float)
        capture_token:  UUID from the page load (for retroactive event update)

    Actions:
        1. Find or create FingerprintIdentity from visitor_id
        2. Link it to the session Identity (if exists)
        3. Retroactively update PAGE_VIEW CaptureEvent with fingerprint data

    Rate limited by RateLimitMiddleware. @csrf_exempt because sendBeacon
    cannot set custom headers — acceptable for low-risk linking.
    """
    try:
        # Parse body — sendBeacon sends as text/plain or application/json
        body = _parse_beacon_body(request)
        visitor_id = (body.get("visitor_id") or "").strip()

        if not visitor_id:
            return JsonResponse(
                {"status": "error", "reason": "missing_visitor_id"}, status=400
            )

        request_id = (body.get("request_id") or "").strip()
        confidence = _parse_float(body.get("confidence"), default=0.0)
        capture_token = (body.get("capture_token") or "").strip()

        # 1. Find or create FingerprintIdentity
        from apps.contacts.fingerprint.models import FingerprintIdentity

        fp_identity, fp_created = FingerprintIdentity.objects.get_or_create(
            hash=visitor_id,
            defaults={
                "confidence_score": confidence,
                "metadata": {"source": "beacon", "request_id": request_id},
            },
        )

        if not fp_created:
            # Update last_seen + metadata on existing fingerprint
            fp_identity.update_last_seen()
            if request_id:
                fp_identity.metadata = {
                    **(fp_identity.metadata or {}),
                    "last_request_id": request_id,
                    "source": "beacon",
                }
                fp_identity.save(update_fields=["metadata", "updated_at"])

        # 2. Link to session Identity
        identity_pk = (
            request.session.get("identity_pk") if hasattr(request, "session") else None
        )
        linked = False

        if identity_pk and not fp_identity.identity_id:
            from apps.contacts.identity.models import Identity

            try:
                session_identity = Identity.objects.get(
                    pk=identity_pk, status=Identity.ACTIVE, is_deleted=False
                )
                fp_identity.identity = session_identity
                fp_identity.save(update_fields=["identity", "updated_at"])
                linked = True

                # Upgrade confidence: fingerprint adds ~0.15
                new_confidence = min(session_identity.confidence_score + 0.15, 1.0)
                if new_confidence > session_identity.confidence_score:
                    session_identity.confidence_score = new_confidence
                    session_identity.save(
                        update_fields=["confidence_score", "updated_at"]
                    )

                logger.info(
                    "fp-resolve: linked %s to identity %s (beacon)",
                    visitor_id[:12],
                    session_identity.public_id,
                )
            except Exception:
                logger.debug("fp-resolve: session identity %s not found", identity_pk)

        elif identity_pk and fp_identity.identity_id:
            # FP already has an identity — check for divergence
            if fp_identity.identity_id != identity_pk:
                # Scenario 3: different identities — dispatch async merge
                from apps.contacts.fingerprint.tasks import (
                    merge_identities_from_fingerprint,
                )

                # Direction normalized inside merge_identities task
                # (oldest survives regardless of argument order)
                merge_identities_from_fingerprint.delay(
                    identity_pk, fp_identity.identity_id
                )
                logger.info(
                    "fp-resolve: divergence detected, merge queued "
                    "(session=%s, fp_identity=%s, fp=%s)",
                    identity_pk,
                    fp_identity.identity_id,
                    visitor_id[:12],
                )

        # 3. Retroactively update PAGE_VIEW event with fingerprint
        events_updated = 0
        if capture_token:
            try:
                capture_uuid = uuid.UUID(capture_token)
                events_updated = CaptureEvent.objects.filter(
                    capture_token=capture_uuid,
                    event_type=CaptureEvent.EventType.PAGE_VIEW,
                    fingerprint_identity__isnull=True,
                ).update(
                    fingerprint_identity=fp_identity,
                    visitor_id=visitor_id,
                )
            except (ValueError, AttributeError):
                logger.debug("fp-resolve: invalid capture_token %s", capture_token[:12])

        return JsonResponse(
            {
                "status": "ok",
                "linked": linked,
                "fp_created": fp_created,
                "events_updated": events_updated,
            }
        )

    except Exception:
        logger.exception("fp-resolve: unexpected error")
        return JsonResponse({"status": "error"}, status=500)


def _parse_beacon_body(request: HttpRequest) -> dict[str, Any]:
    """Parse sendBeacon body — handles JSON, form-encoded, and text/plain.

    sendBeacon typically sends Content-Type: text/plain when using
    JSON.stringify(). We try JSON first, then fall back to form data.
    """
    if request.body:
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # Fallback: form-encoded (unlikely for beacon but safe)
    data = getattr(request, "data", request.POST)
    return dict(data.items()) if hasattr(data, "items") else {}


def _parse_float(value: Any, default: float = 0.0) -> float:
    """Safely parse a float from beacon payload."""
    if value is None:
        return default
    try:
        if isinstance(value, dict):
            # FingerprintJS Pro confidence is {score: 0.999}
            return float(value.get("score", default))
        return float(value)
    except (ValueError, TypeError):
        return default


# ── Capture intent endpoint ────────────────────────────────────────────


@csrf_exempt
@require_POST
def capture_intent(request: HttpRequest) -> HttpResponse:
    """Receive partial form data (email/phone hints) via sendBeacon.

    URL: /api/capture-intent/

    Called by useCaptureIntent hook on field blur — captures form
    abandonment data for visitors who start typing but don't submit.

    Payload (JSON):
        email_hint:     Partial email (valid-looking)
        phone_hint:     Partial phone (>8 digits)
        capture_token:  UUID from the page load

    Actions:
        1. Store hints in Django session (for pre-fill on return)
        2. Upsert a CaptureIntent prelead record
        3. Bind anonymous CaptureEvents to the identity retroactively
        4. Record FORM_INTENT CaptureEvent for funnel analytics

    Rate limited. @csrf_exempt — sendBeacon can't set headers.
    """
    try:
        body = _parse_beacon_body(request)
        email_hint = (body.get("email_hint") or "").strip().lower()
        phone_hint = (body.get("phone_hint") or "").strip()
        capture_token = (body.get("capture_token") or "").strip()
        visitor_id = (body.get("visitor_id") or "").strip()
        request_id = (body.get("request_id") or "").strip()

        if not email_hint and not phone_hint:
            return JsonResponse({"status": "error", "reason": "no_hints"}, status=400)

        # 1. Store hints in session
        if hasattr(request, "session"):
            if email_hint:
                request.session["email_hint"] = email_hint
            if phone_hint:
                request.session["phone_hint"] = phone_hint

        # 2. Resolve current identity context (session identity remains anonymous until submit)
        identity = getattr(request, "identity", None)
        if identity is None and hasattr(request, "session"):
            # Fallback: recover identity from session PK
            identity_pk = request.session.get("identity_pk")
            if identity_pk:
                try:
                    from apps.contacts.identity.models import Identity

                    identity = Identity.objects.get(
                        pk=identity_pk, status=Identity.ACTIVE, is_deleted=False
                    )
                except Exception:
                    logger.debug(
                        "capture-intent: identity PK=%s not found", identity_pk
                    )

        request.identity = identity  # type: ignore[attr-defined]
        intent, intent_created = TrackingService.upsert_capture_intent(
            request=request,
            capture_token=capture_token,
            email_hint=email_hint,
            phone_hint=phone_hint,
            visitor_id=visitor_id,
            request_id=request_id,
        )

        # 3. Bind anonymous events to identity retroactively
        events_bound = 0
        if identity and capture_token:
            try:
                events_bound = TrackingService.bind_events_to_identity(
                    capture_token=capture_token,
                    identity=identity,
                )
            except Exception:
                logger.debug("capture-intent: failed to bind events", exc_info=True)

        # 4. Record FORM_INTENT event
        if capture_token:
            try:
                extra_data: dict[str, Any] = {}
                if email_hint:
                    # Store domain only (not full email) for privacy
                    extra_data["email_domain"] = (
                        email_hint.split("@")[-1] if "@" in email_hint else ""
                    )
                    extra_data["has_email_hint"] = True
                if phone_hint:
                    extra_data["has_phone_hint"] = True
                    # Store country code only (first 3 chars)
                    extra_data["phone_prefix"] = phone_hint[:3]

                # Use Referer as page_path (beacon comes from JS, not the landing page URL)
                referer = request.META.get("HTTP_REFERER", "")
                if referer:
                    from urllib.parse import urlparse

                    page_path = urlparse(referer).path
                else:
                    page_path = request.session.get("last_page", "/")

                TrackingService.create_event(
                    event_type=CaptureEvent.EventType.FORM_INTENT,
                    capture_token=capture_token,
                    page_path=page_path,
                    page_category=CaptureEvent.PageCategory.CAPTURE,
                    request=request,
                    extra_data=extra_data,
                )
            except Exception:
                logger.debug("capture-intent: failed to record event", exc_info=True)

        return JsonResponse(
            {
                "status": "ok",
                "intent_created": intent_created,
                "intent_id": intent.public_id if intent else "",
                "events_bound": events_bound,
            },
            status=202,
        )

    except Exception:
        logger.exception("capture-intent: unexpected error")
        return JsonResponse({"status": "error"}, status=500)


# ── AgreliFlix (CPL video lesson series) ──────────────────────────────

# Miami timezone offset (EST = UTC-5, EDT = UTC-4).
# AgreliFlix dates are stored as naive datetimes in the JSON config and
# are interpreted as US/Eastern (Miami) time. We use a fixed UTC-5 offset
# here; for DST-aware handling, switch to zoneinfo.ZoneInfo("US/Eastern").
_MIAMI_TZ = timezone(timedelta(hours=-5))


def _parse_agrelliflix_episodes(
    raw_episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Parse episode dates server-side and compute availability flags.

    Converts naive ``live_date`` strings into timezone-aware ISO 8601
    strings and computes ``available_at``, ``expires_at``, and
    ``is_live_pending`` for each episode so the frontend doesn't need
    date math.

    Args:
        raw_episodes: Episode dicts from the campaign JSON.

    Returns:
        Episodes with computed date fields as ISO 8601 strings.
    """
    now = datetime.now(tz=_MIAMI_TZ)
    parsed: list[dict[str, Any]] = []

    for ep in raw_episodes:
        episode = dict(ep)  # shallow copy — don't mutate cached config

        # Parse live_date as Miami time
        live_date_str = episode.get("live_date", "")
        if live_date_str:
            naive = datetime.fromisoformat(live_date_str)
            live_dt = naive.replace(tzinfo=_MIAMI_TZ)
        else:
            live_dt = now  # fallback: treat as already available

        # Compute available_at / expires_at
        available_days: int = episode.get("available_days_from_now", 0)
        expires_days: int = episode.get("expires_days_from_now", 7)

        if available_days == 0:
            available_at = live_dt
        else:
            available_at = now + timedelta(days=available_days)

        expires_at = live_dt + timedelta(days=expires_days)

        # Flags
        is_live_pending = now < live_dt
        is_available = available_at <= now < expires_at
        is_expired = now >= expires_at

        # Inject computed fields
        episode["available_at"] = available_at.isoformat()
        episode["expires_at"] = expires_at.isoformat()
        episode["live_date"] = live_dt.isoformat()
        episode["is_live_pending"] = is_live_pending
        episode["is_available"] = is_available
        episode["is_expired"] = is_expired

        parsed.append(episode)

    return parsed


def _parse_agrelliflix_cart(cart: dict[str, Any]) -> dict[str, Any]:
    """Parse cart open date and compute ``is_cart_open`` flag.

    Args:
        cart: Cart config dict from the campaign JSON.

    Returns:
        Cart dict with ``open_date`` as ISO 8601 and ``is_open`` flag.
    """
    now = datetime.now(tz=_MIAMI_TZ)
    result = dict(cart)

    open_date_str = result.get("open_date", "")
    if open_date_str:
        naive = datetime.fromisoformat(open_date_str)
        open_dt = naive.replace(tzinfo=_MIAMI_TZ)
        result["open_date"] = open_dt.isoformat()
        result["is_open"] = now >= open_dt
    else:
        result["is_open"] = False

    return result


@require_GET
def agrelliflix_page(
    request: HttpRequest,
    episode_number: int = 0,
) -> HttpResponse:
    """Render the AgreliFlix video lesson page.

    URLs:
      /agrelliflix/                → episode_number=0 (main page, auto-select)
      /agrelliflix-aula-1/        → episode_number=1
      /agrelliflix-aula-2/        → episode_number=2
      /agrelliflix-aula-3/        → episode_number=3
      /agrelliflix-aula-4/        → episode_number=4

    Config is loaded from ``campaigns/agrelliflix.json`` (cached in memory).
    Episode dates are parsed server-side (Miami timezone) so the frontend
    receives ready-to-use ISO 8601 strings with availability flags.
    """
    config = get_campaign("agrelliflix")
    if config is None:
        logger.warning("agrelliflix: campaign config not found, redirecting to home")
        return redirect("/")

    # Parse episodes and cart dates server-side
    raw_episodes: list[dict[str, Any]] = config.get("episodes", [])
    episodes = _parse_agrelliflix_episodes(raw_episodes)
    cart = _parse_agrelliflix_cart(config.get("cart", {}))

    # Determine initial episode (0 = auto-select first available)
    initial_episode_id = episode_number
    if initial_episode_id == 0:
        # Auto-select: first available episode, or episode 1
        for ep in episodes:
            if ep.get("is_available") and not ep.get("is_live_pending"):
                initial_episode_id = ep["id"]
                break
        else:
            initial_episode_id = 1

    # Page name for tracking (matches legacy)
    page_name = (
        "agrelliflix" if episode_number == 0 else f"agrelliflix-aula-{episode_number}"
    )

    # Track page_view event
    try:
        capture_token = TrackingService.generate_capture_token()
        TrackingService.create_event(
            event_type=CaptureEvent.EventType.PAGE_VIEW,
            capture_token=capture_token,
            page_path=request.path,
            page_category=CaptureEvent.PageCategory.CONTENT,
            request=request,
        )
    except Exception:
        logger.debug("agrelliflix: failed to track page_view for %s", page_name)

    # Build props for Inertia (frontend receives ready-to-use data)
    props: dict[str, Any] = {
        "config": {
            "slug": config.get("slug", "agrelliflix"),
            "meta": config.get("meta", {}),
            "branding": config.get("branding", {}),
            "theme": config.get("theme", {}),
            "episodes": episodes,
            "achievements": config.get("achievements", {}),
            "ctas": config.get("ctas", {}),
            "social_proof": config.get("social_proof", {}),
            "cart": cart,
            "whatsapp": config.get("whatsapp", {}),
            "banner_urls": config.get("banner_urls", {}),
            "tracking": config.get("tracking", {}),
        },
        "initial_episode_id": initial_episode_id,
        "page_name": page_name,
    }

    return inertia_render(request, "AgreliFlix/Index", props, app="landing")


# ── Placeholder routes (legacy parity) ────────────────────────────────
# These routes exist in the legacy Next.js project and must return a
# response (not 404) for SEO/link parity. Pages that aren't yet ported
# to Inertia redirect to the default capture page.


@require_GET
def support_launch_page(request: HttpRequest) -> HttpResponse:
    """Support page with video background and Chatwoot auto-open.

    URL: /suporte-launch/

    Legacy: auto-opens Chatwoot with UTM context over a YouTube
    video background. Has enrollment CTA at the bottom.

    Config is site-wide (not per-campaign). Tracks page_view event.
    """
    _track_page_view(request, "/suporte-launch/", CaptureEvent.PageCategory.SUPPORT)

    config = LandingPageConfigService.get_support_launch_config()

    return inertia_render(
        request,
        "SuporteLaunch/Index",
        {"config": config},
        app="landing",
    )


@require_GET
def onboarding_page(request: HttpRequest) -> HttpResponse:
    """Post-purchase onboarding page.

    URL: /onboarding/

    Shows a marquee header confirming purchase, instructional video,
    and WhatsApp floating button. Content is config-driven.

    Legacy: frontend-landing-pages/app/onboarding/page.tsx (158 lines)
    """
    _track_page_view(request, "/onboarding/", CaptureEvent.PageCategory.CONTENT)

    config = LandingPageConfigService.get_onboarding_config()

    return inertia_render(
        request,
        "Onboarding/Index",
        {"config": config},
        app="landing",
    )


@require_GET
def lembrete_bf_page(request: HttpRequest) -> HttpResponse:
    """Black Friday reminder page.

    URL: /lembrete-bf/

    Urgency-driven page with countdown timer, course cards, bonus tiers,
    pricing comparison, and WhatsApp CTA. All content is config-driven.

    Legacy: frontend-landing-pages/app/lembrete-bf/page.tsx (676 lines)
    """
    _track_page_view(request, "/lembrete-bf/", CaptureEvent.PageCategory.CONTENT)

    config = LandingPageConfigService.get_lembrete_bf_config()

    return inertia_render(
        request,
        "LembreteBF/Index",
        {"config": config},
        app="landing",
    )


@require_GET
def recado_importante_page(request: HttpRequest) -> HttpResponse:
    """Long-form sales page (VSL).

    URL: /recado-importante/

    Vertical sales letter with hero video, expert card, video testimonials,
    course modules, bonuses, mega bonus, pricing reveal, and floating CTA.
    All content is config-driven.

    Legacy: frontend-landing-pages/app/recado-importante/ (~2,800 lines / 27 files)
    """
    _track_page_view(request, "/recado-importante/", CaptureEvent.PageCategory.CONTENT)

    config = LandingPageConfigService.get_recado_importante_config()

    return inertia_render(
        request,
        "RecadoImportante/Index",
        {"config": config},
        app="landing",
    )
