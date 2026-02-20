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
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.inertia.helpers import inertia_render
from core.tracking.models import CaptureEvent
from core.tracking.services import DeviceProfileService, TrackingService

from apps.ads.models import CaptureSubmission
from apps.ads.services.utm_parser import UTMParserService
from apps.landing.campaigns import get_campaign, get_campaign_or_default
from apps.landing.services.capture import CaptureService
from apps.landing.tasks import send_to_n8n_task
from apps.launches.services import CapturePageService

logger = logging.getLogger(__name__)

# Default campaign slug — used as fallback for non-existent slugs.
DEFAULT_CAMPAIGN_SLUG = "wh-rc-v3"


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

    # Fallback to JSON files (migration period)
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
        default_config = get_campaign_or_default(campaign_slug)
        frontend_props = default_config
        backend_config = default_config

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
    fingerprint_api_key = os.getenv("FINGERPRINT_API_KEY", "")
    fingerprint_endpoint = os.getenv("FINGERPRINT_ENDPOINT", "")

    props: dict[str, Any] = {
        "campaign": _build_campaign_props(campaign, campaign_slug),
        "fingerprint_api_key": fingerprint_api_key,
        "fingerprint_endpoint": fingerprint_endpoint,
        "capture_token": capture_token,
    }

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
            # Get primary email
            primary_email = (
                identity.email_contacts.filter(is_deleted=False)
                .order_by("-is_primary", "-created_at")
                .values_list("value", flat=True)
                .first()
            )
            if primary_email:
                prefill["email"] = primary_email

            # Get primary phone
            primary_phone = (
                identity.phone_contacts.filter(is_deleted=False)
                .order_by("-is_primary", "-created_at")
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

    After identity resolution, parses UTMs via UTMParserService and
    creates a CaptureSubmission (star schema fact table) with all
    resolved dimension FKs.

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
            identity_public_id=getattr(request, "identity_public_id", ""),
            errors=errors,
        )

    # Extract form fields
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    visitor_id = data.get("visitor_id") or data.get("fingerprint") or ""
    request_id = data.get("request_id") or data.get("eventid") or ""

    # Extract UTM data
    utm_data: dict[str, str] = {
        "utm_source": data.get("utm_source", ""),
        "utm_medium": data.get("utm_medium", ""),
        "utm_campaign": data.get("utm_campaign", ""),
        "utm_content": data.get("utm_content", ""),
        "utm_term": data.get("utm_term", ""),
        "utm_id": data.get("utm_id", ""),
    }

    # Extract ad tracking params (Meta CAPI, Voluum)
    extra_ad_params: dict[str, str] = {
        "fbclid": data.get("fbclid", ""),
        "vk_ad_id": data.get("vk_ad_id", ""),
        "vk_source": data.get("vk_source", ""),
    }

    page_url = request.build_absolute_uri()
    referrer = request.META.get("HTTP_REFERER", "")

    # Session-based identity: may already exist from IdentitySessionMiddleware
    session_identity = getattr(request, "identity", None)

    # Process the lead (identity resolution + attribution)
    # Uses backend_config which includes n8n keys
    # Passes session_identity so resolution can enrich it instead of creating new
    result = CaptureService.process_lead(
        email=email,
        phone=phone,
        visitor_id=visitor_id,
        request_id=request_id,
        utm_data=utm_data,
        campaign_config=backend_config,
        page_url=page_url,
        referrer=referrer,
        session_identity=session_identity,
    )

    # Track form success
    TrackingService.create_event(
        event_type=CaptureEvent.EventType.FORM_SUCCESS,
        capture_token=capture_token,
        page_path=page_path,
        page_category=CaptureEvent.PageCategory.CAPTURE,
        request=request,
        capture_page=capture_page_model,
        extra_data={"email_domain": email.split("@")[-1] if "@" in email else ""},
    )

    # Bind anonymous events to resolved identity (retroactive)
    identity = result.get("identity")
    if identity is not None:
        TrackingService.bind_events_to_identity(
            capture_token=capture_token,
            identity=identity,
            visitor_id=visitor_id,
        )

    # Mark Django session as converted (extends TTL to 365d)
    TrackingService.mark_session_converted(request, email=email)

    # Update session identity_pk if resolution returned a different identity
    # (e.g., merged with existing email-based identity)
    if identity is not None and hasattr(request, "session"):
        request.session["identity_pk"] = identity.pk
        request.session["identity_id"] = identity.public_id

    # Update Redis capture session status (short-lived, event correlation)
    TrackingService.update_capture_session(
        capture_token=capture_token,
        updates={
            "status": "converted",
            "email_domain": email.split("@")[-1] if "@" in email else "",
        },
    )

    # ── Create CaptureSubmission (star schema fact table) ─────────
    submission = None
    if identity is not None and capture_page_model is not None:
        submission = _create_capture_submission(
            identity=identity,
            email_raw=data.get("email", ""),
            phone_raw=data.get("phone", ""),
            capture_page=capture_page_model,
            utm_data=utm_data,
            extra_ad_params=extra_ad_params,
            capture_token=capture_token,
            visitor_id=visitor_id,
            request=request,
            t_start=t_start,
        )

    # Fire N8N webhook asynchronously via Celery
    n8n_webhook_url = result.get("n8n_webhook_url", "")
    n8n_payload = result.get("n8n_payload", {})
    if n8n_webhook_url:
        submission_id = submission.public_id if submission else ""
        send_to_n8n_task.delay(n8n_webhook_url, n8n_payload, submission_id)

    # Redirect to thank-you page
    thank_you_url = backend_config.get("form", {}).get(
        "thank_you_url",
        backend_config.get("thank_you", {}).get(
            "url", f"/obrigado-{backend_config.get('slug', campaign_slug)}/"
        ),
    )
    return redirect(thank_you_url)


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
    """Parse UTMs and create a CaptureSubmission fact record.

    Resilient: if parsing or submission creation fails, logs error
    and returns None (never blocks the redirect).

    Args:
        identity: Resolved Identity instance.
        email_raw: Raw email from form (before normalization).
        phone_raw: Raw phone from form.
        capture_page: CapturePage model instance.
        utm_data: Standard UTM parameters.
        extra_ad_params: fbclid, vk_ad_id, vk_source.
        capture_token: UUID linking to CaptureEvents.
        visitor_id: FingerprintJS visitorId.
        request: HttpRequest (for device_profile, ip, geo).
        t_start: time.monotonic() from start of POST handler.
    """
    try:
        # Parse UTMs and resolve all dimension FKs
        launch = getattr(capture_page, "launch", None)
        parsed = UTMParserService.parse(
            utm_data,
            extra_ad_params,
            launch=launch,
        )

        # Calculate server render time
        server_render_time_ms = (time.monotonic() - t_start) * 1000

        # Resolve device profile from request (VisitorMiddleware)
        device_profile = DeviceProfileService.get_or_create_from_request(request)

        # Extract network data from request
        ip_address = getattr(request, "client_ip", None) or None
        geo_data = getattr(request, "geo_data", {})

        # Detect duplicate (same email + same launch)
        is_duplicate = False
        if launch is not None:
            is_duplicate = CaptureSubmission.objects.filter(
                email_raw__iexact=email_raw.strip(),
                capture_page__launch=launch,
                is_deleted=False,
            ).exists()

        # Parse capture_token to UUID (may be string from form)
        try:
            capture_token_uuid = uuid.UUID(capture_token)
        except (ValueError, AttributeError):
            capture_token_uuid = uuid.uuid4()

        # Click ID: from parsed result or direct from extra_params
        click_id = parsed.click_id or extra_ad_params.get("fbclid", "")

        submission = CaptureSubmission.objects.create(
            identity=identity,
            email_raw=email_raw,
            phone_raw=phone_raw,
            capture_page=capture_page,
            traffic_source=parsed.traffic_source,
            ad_group=parsed.ad_group,
            ad_creative=parsed.creative,
            click_id=click_id,
            visitor_id=visitor_id,
            capture_token=capture_token_uuid,
            device_profile=device_profile,
            ip_address=ip_address,
            geo_data=geo_data or {},
            n8n_status="pending",
            server_render_time_ms=server_render_time_ms,
            is_duplicate=is_duplicate,
            raw_utm_data={**utm_data, **extra_ad_params},
        )

        logger.info(
            "CaptureSubmission created: %s (email=%s, page=%s, duplicate=%s)",
            submission.public_id,
            email_raw[:20],
            capture_page.slug,
            is_duplicate,
        )
        return submission

    except Exception:
        logger.exception(
            "Failed to create CaptureSubmission (email=%s, page=%s)",
            email_raw[:20],
            getattr(capture_page, "slug", "?"),
        )
        return None


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

                # Merge direction: session identity (newer, anonymous) → FP identity (older, richer)
                # Oldest survives — let the task figure out direction
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
        2. Record FORM_INTENT CaptureEvent for funnel analytics

    Rate limited. @csrf_exempt — sendBeacon can't set headers.
    """
    try:
        body = _parse_beacon_body(request)
        email_hint = (body.get("email_hint") or "").strip().lower()
        phone_hint = (body.get("phone_hint") or "").strip()
        capture_token = (body.get("capture_token") or "").strip()

        if not email_hint and not phone_hint:
            return JsonResponse({"status": "error", "reason": "no_hints"}, status=400)

        # 1. Store hints in session
        if hasattr(request, "session"):
            if email_hint:
                request.session["email_hint"] = email_hint
            if phone_hint:
                request.session["phone_hint"] = phone_hint

        # 2. Record FORM_INTENT event
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

                TrackingService.create_event(
                    event_type=CaptureEvent.EventType.FORM_INTENT,
                    capture_token=capture_token,
                    page_path=request.session.get("last_page", "/"),
                    page_category=CaptureEvent.PageCategory.CAPTURE,
                    request=request,
                    extra_data=extra_data,
                )
            except Exception:
                logger.debug("capture-intent: failed to record event", exc_info=True)

        return JsonResponse({"status": "ok"})

    except Exception:
        logger.exception("capture-intent: unexpected error")
        return JsonResponse({"status": "error"}, status=500)


# ── Placeholder routes (legacy parity) ────────────────────────────────
# These routes exist in the legacy Next.js project and must return a
# response (not 404) for SEO/link parity. Pages that aren't yet ported
# to Inertia redirect to the default capture page.


@require_GET
def support_launch_page(request: HttpRequest) -> HttpResponse:
    """Support page variant for active launches.

    URL: /suporte-launch/

    Legacy: auto-opens Chatwoot with UTM context.
    Currently: same as /suporte/ (shared support page).
    """
    return support_page(request)


@require_GET
def placeholder_redirect(request: HttpRequest) -> HttpResponse:
    """Redirect placeholder for legacy routes not yet ported.

    Used for: /lembrete-bf/, /recado-importante/, /onboarding/,
    /agrelliflix/, /agrelliflix-aula-{1..4}/.

    These are complex pages (sales funnels, video platforms,
    post-purchase flows) that will be implemented in later phases.

    Tracks page_view event for visitor journey attribution before redirect.
    """
    _track_redirect(request, request.path)
    return redirect("/")
