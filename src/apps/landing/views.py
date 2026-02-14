"""
Landing page views.

Capture views handle both GET (render landing page) and POST (process form).
All landing views use app="landing" for the landing.html Inertia template.
"""

import logging
import os
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from core.inertia.helpers import inertia_render

from apps.landing.campaigns import get_campaign_or_default
from apps.landing.services.capture import CaptureService
from apps.landing.tasks import send_to_n8n_task

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """Landing home page — placeholder for Phase C smoke test."""
    return inertia_render(
        request,
        "Home/Index",
        {
            "title": "Arthur Agrelli",
            "description": "Plataforma de lancamentos digitais. Em breve.",
        },
        app="landing",
    )


def capture_page(request: HttpRequest, campaign_slug: str) -> HttpResponse:
    """Capture landing page — GET renders form, POST processes lead.

    URL: /inscrever/<campaign_slug>/

    GET: Serves the landing page with campaign config as Inertia props.
    POST: Validates form, resolves identity, forwards to N8N, redirects.
    """
    campaign = get_campaign_or_default(campaign_slug)

    if request.method == "POST":
        return _handle_capture_post(request, campaign, campaign_slug)

    return _render_capture_page(request, campaign, campaign_slug)


def _build_campaign_props(
    campaign: dict[str, Any], campaign_slug: str
) -> dict[str, Any]:
    """Build the campaign props dict for the Capture page.

    Includes all visual-parity fields (background_image, highlight_color,
    subheadline, button_gradient) used by the dark-theme landing frontend.
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
    for field in ("subheadline", "background_image", "highlight_color"):
        value = campaign.get(field)
        if value is not None:
            props[field] = value

    return props


def _render_capture_page(
    request: HttpRequest,
    campaign: dict[str, Any],
    campaign_slug: str,
    *,
    errors: dict[str, str] | None = None,
) -> HttpResponse:
    """Render the Capture/Index page with campaign props.

    When errors are provided (POST validation failure), re-renders the
    page with errors as props so the frontend can display them inline.
    """
    fingerprint_api_key = os.getenv("FINGERPRINT_API_KEY", "")

    props: dict[str, Any] = {
        "campaign": _build_campaign_props(campaign, campaign_slug),
        "fingerprint_api_key": fingerprint_api_key,
    }

    if errors:
        props["errors"] = errors

    return inertia_render(request, "Capture/Index", props, app="landing")


def _handle_capture_post(
    request: HttpRequest, campaign: dict[str, Any], campaign_slug: str
) -> HttpResponse:
    """Handle capture form POST submission.

    Uses request.data (parsed by InertiaJsonParserMiddleware).
    Re-renders page with errors on validation failure,
    or redirects to thank-you URL on success.
    """
    data = getattr(request, "data", request.POST)

    # Server-side validation
    errors = CaptureService.validate_form_data(data)
    if errors:
        return _render_capture_page(request, campaign, campaign_slug, errors=errors)

    # Extract form fields
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    visitor_id = data.get("visitor_id") or data.get("fingerprint") or ""
    request_id = data.get("request_id") or data.get("eventid") or ""

    # Extract UTM data
    utm_data = {
        "utm_source": data.get("utm_source", ""),
        "utm_medium": data.get("utm_medium", ""),
        "utm_campaign": data.get("utm_campaign", ""),
        "utm_content": data.get("utm_content", ""),
        "utm_term": data.get("utm_term", ""),
        "utm_id": data.get("utm_id", ""),
    }

    page_url = request.build_absolute_uri()
    referrer = request.META.get("HTTP_REFERER", "")

    # Process the lead (identity resolution + attribution)
    result = CaptureService.process_lead(
        email=email,
        phone=phone,
        visitor_id=visitor_id,
        request_id=request_id,
        utm_data=utm_data,
        campaign_config=campaign,
        page_url=page_url,
        referrer=referrer,
    )

    # Fire N8N webhook asynchronously via Celery
    n8n_webhook_url = result.get("n8n_webhook_url", "")
    n8n_payload = result.get("n8n_payload", {})
    if n8n_webhook_url:
        send_to_n8n_task.delay(n8n_webhook_url, n8n_payload)

    # Redirect to thank-you page
    thank_you_url = campaign.get("form", {}).get(
        "thank_you_url", f"/obrigado/{campaign.get('slug', '')}/"
    )
    return redirect(thank_you_url)


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
    """
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

    URL: /terms/
    """
    return inertia_render(request, "Legal/Terms", {}, app="landing")


@require_GET
def privacy_page(request: HttpRequest) -> HttpResponse:
    """Privacy Policy page.

    URL: /privacy/
    """
    return inertia_render(request, "Legal/Privacy", {}, app="landing")


@require_GET
def thank_you_page(request: HttpRequest, campaign_slug: str) -> HttpResponse:
    """Thank-you page after successful capture.

    URL: /obrigado/<campaign_slug>/

    Renders urgency-driven page with WhatsApp CTA, countdown timer,
    and progress bar. Config comes from campaign JSON ``thank_you`` key.
    """
    campaign = get_campaign_or_default(campaign_slug)
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
