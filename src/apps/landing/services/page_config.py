"""Landing page configuration service.

Centralizes page config generation for config-driven Inertia pages.
This allows easier maintenance, testing, and future CMS integration.
"""

from typing import Any, TypedDict

from django.conf import settings

from apps.landing.campaigns import get_campaign


# =============================================================================
# TypedDict definitions for type safety
# =============================================================================


class ChatwootConfig(TypedDict):
    """Chatwoot widget configuration."""

    website_token: str
    base_url: str
    locale: str
    header_title: str
    header_subtitle: str
    business_hours: str


class ChatwootMinimalConfig(TypedDict):
    """Minimal Chatwoot config for pages that auto-open widget."""

    website_token: str
    base_url: str
    locale: str


class SuporteLaunchConfig(TypedDict):
    """Configuration for /suporte-launch/ page."""

    video_id: str
    title: str
    subtitle: str
    cta_link: str
    cta_text: str
    chatwoot: ChatwootMinimalConfig


class OnboardingConfig(TypedDict):
    """Configuration for /onboarding/ page."""

    video_id: str
    title: str
    marquee_items: list[str]
    marquee_color: str
    background_image: str
    whatsapp_link: str


class CourseCard(TypedDict):
    """Course card in LembreteBF."""

    title: str
    description: str
    image: str


class BonusTier(TypedDict):
    """Bonus tier in LembreteBF."""

    tier: str
    title: str
    description: str


class PriceLabel(TypedDict):
    """Price label for comparison table."""

    label: str
    value: str


class LembreteBFImages(TypedDict):
    """Image paths for LembreteBF."""

    logo: str


class LembreteBFConfig(TypedDict):
    """Configuration for /lembrete-bf/ page."""

    target_date: str
    cta_link: str
    cta_text: str
    headline: str
    benefits: list[str]
    courses: list[CourseCard]
    bonuses: list[BonusTier]
    normal_prices: list[PriceLabel]
    special_price: str
    installments_text: str
    images: LembreteBFImages


class ExpertInfo(TypedDict):
    """Expert/instructor info for sales page."""

    name: str
    title: str
    description: str
    image: str


class TestimonialVideo(TypedDict):
    """Video testimonial entry."""

    video_id: str
    name: str
    description: str


class CourseModule(TypedDict):
    """Course module description."""

    title: str
    description: str


class BonusItem(TypedDict):
    """Bonus item with value."""

    title: str
    description: str
    value: str


class MegaBonus(TypedDict):
    """Mega bonus highlight."""

    title: str
    description: str
    value: str


class PricingInfo(TypedDict):
    """Pricing section info."""

    original_price: str
    current_price: str
    installments_text: str
    discount_text: str


class RecadoImportanteImages(TypedDict):
    """Image paths for RecadoImportante."""

    hero_bg: str


class RecadoImportanteConfig(TypedDict):
    """Configuration for /recado-importante/ page."""

    video_id: str
    cta_link: str
    cta_text: str
    target_date: str
    expert: ExpertInfo
    testimonials: list[TestimonialVideo]
    course_description: str
    modules: list[CourseModule]
    bonuses: list[BonusItem]
    mega_bonus: MegaBonus
    pricing: PricingInfo
    images: RecadoImportanteImages


class AgrelliFlixConfig(TypedDict, total=False):
    """Configuration for the AgrelliFlix content experience."""

    slug: str
    meta: dict[str, Any]
    branding: dict[str, Any]
    theme: dict[str, Any]
    episodes: list[dict[str, Any]]
    achievements: dict[str, Any]
    cart: dict[str, Any]


# =============================================================================
# Service class
# =============================================================================


class LandingPageConfigService:
    """Service for generating landing page configurations.

    Extracts hardcoded config dictionaries from views into a service layer,
    following the project's service-layer architecture pattern.
    """

    @staticmethod
    def _get_chatwoot_base_config() -> ChatwootConfig:
        """Return base Chatwoot configuration using Django settings.

        Returns:
            ChatwootConfig with website_token, base_url, locale, and display strings.
        """
        return {
            "website_token": settings.CHATWOOT_WEBSITE_TOKEN,
            "base_url": settings.CHATWOOT_BASE_URL,
            "locale": "pt_BR",
            "header_title": "Suporte Arthur Agrelli",
            "header_subtitle": "Online",
            "business_hours": (
                "Suporte disponivel de Segunda a Sexta, das 9h as 18h (Horario de Brasilia)"
            ),
        }

    @staticmethod
    def get_chatwoot_config() -> ChatwootConfig:
        """Return site-wide Chatwoot configuration.

        Returns:
            ChatwootConfig with website_token, base_url, locale, and display strings.
        """
        return LandingPageConfigService._get_chatwoot_base_config()

    @staticmethod
    def get_support_launch_config() -> SuporteLaunchConfig:
        """Return SuporteLaunch page configuration.

        URL: /suporte-launch/

        Config for support page with video background and Chatwoot auto-open.
        Has enrollment CTA at the bottom.

        Returns:
            SuporteLaunchConfig with video_id, title, subtitle, cta_link, cta_text, chatwoot.
        """
        chatwoot = LandingPageConfigService._get_chatwoot_base_config()
        return {
            "video_id": "xLQdQmmt_Kc",
            "title": "Suporte Oficial",
            "subtitle": "Nosso time de especialistas está pronto para te ajudar.",
            "cta_link": "/inscrever-wh-rc-v3/",
            "cta_text": "QUERO ME INSCREVER",
            "chatwoot": {
                "website_token": chatwoot["website_token"],
                "base_url": chatwoot["base_url"],
                "locale": chatwoot["locale"],
            },
        }

    @staticmethod
    def get_onboarding_config() -> OnboardingConfig:
        """Return Onboarding page configuration.

        URL: /onboarding/

        Config for post-purchase onboarding page with marquee header,
        instructional video, and WhatsApp floating button.

        Returns:
            OnboardingConfig with video_id, title, marquee_items, colors, and links.
        """
        return {
            # TODO(content-team): Replace with production video ID
            "video_id": "dQw4w9WgXcQ",
            "title": "Libere Seu Acesso Agora!",
            "marquee_items": [
                "PARABÉNS PELA SUA COMPRA!",
                "ASSISTA O VÍDEO ABAIXO PARA LIBERAR SEU ACESSO",
                "BEM-VINDO AO MÉTODO iREI",
            ],
            "marquee_color": "#16a34a",
            "background_image": "/static/images/bg-eua-flag-dark.jpg",
            "whatsapp_link": "https://go.arthuragrelli.com/wpp-mestre-das-casas-baratas",
        }

    @staticmethod
    def get_lembrete_bf_config() -> LembreteBFConfig:
        """Return LembreteBF page configuration.

        URL: /lembrete-bf/

        Config for Black Friday reminder page with countdown timer,
        course cards, bonus tiers, pricing comparison, and WhatsApp CTA.

        Returns:
            LembreteBFConfig with target_date, cta, headline, benefits, courses, bonuses, pricing.
        """
        return {
            "target_date": "2026-11-29T23:59:00-05:00",
            "cta_link": "https://go.arthuragrelli.com/wpp-bf",
            "cta_text": "GARANTIR MINHA VAGA AGORA",
            "headline": "Última chance de garantir o Método iREI com desconto Black Friday!",
            "benefits": [
                "Acesso completo ao Método iREI",
                "Mentoria em grupo semanal",
                "Comunidade exclusiva de alunos",
                "Garantia incondicional de 7 dias",
            ],
            "courses": [
                {
                    "title": "Método iREI — Repasse de Contratos",
                    "description": "Aprenda a ganhar +$10mil/mês repassando casas sem investir.",
                    "image": "/static/images/bf-course-repasse.jpg",
                },
                {
                    "title": "Tax Deed — Leilão de Imóveis",
                    "description": "Compre imóveis por centavos de dólar em leilões fiscais.",
                    "image": "/static/images/bf-course-taxdeed.jpg",
                },
            ],
            "bonuses": [
                {
                    "tier": "BÔNUS 1",
                    "title": "Planilha de Análise de Deals",
                    "description": "Ferramenta exclusiva para avaliar oportunidades rapidamente.",
                },
                {
                    "tier": "BÔNUS 2",
                    "title": "Scripts de Negociação",
                    "description": "Roteiros prontos para fechar negócios com vendedores motivados.",
                },
                {
                    "tier": "BÔNUS 3",
                    "title": "Acesso ao Grupo VIP",
                    "description": "Networking com alunos ativos que já estão faturando.",
                },
            ],
            "normal_prices": [
                {"label": "Método iREI", "value": "R$ 4.997"},
                {"label": "Mentoria em Grupo", "value": "R$ 2.997"},
                {"label": "Comunidade VIP", "value": "R$ 997"},
                {"label": "Bônus Exclusivos", "value": "R$ 1.497"},
            ],
            "special_price": "R$ 2.997",
            "installments_text": "ou 12x de R$ 297,25",
            "images": {
                "logo": "/static/images/bf-logo.png",
            },
        }

    @staticmethod
    def get_recado_importante_config() -> RecadoImportanteConfig:
        """Return RecadoImportante page configuration.

        URL: /recado-importante/

        Config for long-form sales page (VSL) with hero video, expert card,
        video testimonials, course modules, bonuses, mega bonus, pricing reveal,
        and floating CTA.

        Returns:
            RecadoImportanteConfig with video_id, cta, expert, testimonials, modules, bonuses, pricing.
        """
        return {
            # TODO(content-team): Replace with production video ID
            "video_id": "dQw4w9WgXcQ",
            "cta_link": "https://go.arthuragrelli.com/wpp-mestre-das-casas-baratas",
            "cta_text": "QUERO GARANTIR MINHA VAGA",
            "target_date": "2026-02-28T23:59:00-05:00",
            "expert": {
                "name": "Arthur Agrelli",
                "title": "Especialista em Investimento Imobiliário nos EUA",
                "description": (
                    "Arthur Agrelli é investidor imobiliário nos EUA há mais de 5 anos. "
                    "Já ajudou +5.000 alunos brasileiros a ganhar em dólar repassando "
                    "casas sem tirar dinheiro do bolso."
                ),
                "image": "/static/images/arthur-expert.jpg",
            },
            "testimonials": [
                {
                    # TODO(content-team): Replace with production video ID
                    "video_id": "dQw4w9WgXcQ",
                    "name": "João Silva",
                    "description": "Primeiro repasse em 30 dias",
                },
                {
                    # TODO(content-team): Replace with production video ID
                    "video_id": "dQw4w9WgXcQ",
                    "name": "Maria Souza",
                    "description": "Saiu do zero e faturou $15mil",
                },
                {
                    # TODO(content-team): Replace with production video ID
                    "video_id": "dQw4w9WgXcQ",
                    "name": "Carlos Lima",
                    "description": "$10mil/mês em 3 meses",
                },
                {
                    # TODO(content-team): Replace with production video ID
                    "video_id": "dQw4w9WgXcQ",
                    "name": "Ana Costa",
                    "description": "Mudou de vida morando no Brasil",
                },
            ],
            "course_description": (
                "<p>O <strong>Método iREI</strong> é o sistema mais completo de "
                "investimento imobiliário nos EUA para brasileiros. Você vai aprender "
                "a <strong>ganhar +$10mil por mês</strong> repassando casas sem investir "
                "seu próprio dinheiro.</p>"
            ),
            "modules": [
                {
                    "title": "Módulo 1 — Fundamentos",
                    "description": "Entenda o mercado imobiliário americano e como lucrar.",
                },
                {
                    "title": "Módulo 2 — Encontrar Deals",
                    "description": "Técnicas para encontrar casas abaixo do valor de mercado.",
                },
                {
                    "title": "Módulo 3 — Análise de Propriedades",
                    "description": "Como avaliar se um deal vale a pena em minutos.",
                },
                {
                    "title": "Módulo 4 — Negociação",
                    "description": "Scripts e estratégias para fechar contratos.",
                },
                {
                    "title": "Módulo 5 — Repasse (Wholesale)",
                    "description": "O passo a passo para repassar e lucrar.",
                },
                {
                    "title": "Módulo 6 — Escalar",
                    "description": "Como montar um time e fazer múltiplos deals por mês.",
                },
            ],
            "bonuses": [
                {
                    "title": "Planilha de Análise de Deals",
                    "description": "Ferramenta exclusiva para avaliar oportunidades.",
                    "value": "R$ 997",
                },
                {
                    "title": "Scripts de Negociação Prontos",
                    "description": "Roteiros testados para fechar negócios.",
                    "value": "R$ 497",
                },
                {
                    "title": "Acesso à Comunidade VIP",
                    "description": "Networking com alunos que já estão faturando.",
                    "value": "R$ 1.497",
                },
            ],
            "mega_bonus": {
                "title": "Mentoria em Grupo Semanal",
                "description": (
                    "Tire suas dúvidas diretamente com nossa equipe toda semana. "
                    "Acompanhamento personalizado para acelerar seus resultados."
                ),
                "value": "R$ 2.997",
            },
            "pricing": {
                "original_price": "R$ 10.488",
                "current_price": "R$ 2.997",
                "installments_text": "ou 12x de R$ 297,25",
                "discount_text": "Economia de mais de R$ 7.000",
            },
            "images": {
                "hero_bg": "/static/images/bg-eua-flag-dark.jpg",
            },
        }

    @staticmethod
    def get_agrelliflix_config() -> AgrelliFlixConfig | None:
        """Return AgrelliFlix config from its dedicated legacy JSON source.

        AgrelliFlix is a content/CPL experience that remains intentionally
        outside the standard capture-page runtime. Centralizing the load here
        makes that exception explicit and keeps JSON usage out of the view.
        """
        return get_campaign("agrelliflix")
