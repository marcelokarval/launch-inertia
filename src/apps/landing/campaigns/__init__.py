"""
Campaign configuration loader.

Campaigns are stored as JSON fixtures in this directory.
In the future (Phase G.2), they will migrate to Django models.
"""

import json
from pathlib import Path
from typing import Any

_CAMPAIGNS_DIR = Path(__file__).parent
_cache: dict[str, dict[str, Any]] = {}


def get_campaign(slug: str) -> dict[str, Any] | None:
    """Load a campaign configuration by slug.

    Args:
        slug: Campaign identifier (e.g., "wh-rc-v3").

    Returns:
        Campaign config dict, or None if not found.
    """
    if slug in _cache:
        return _cache[slug]

    config_path = _CAMPAIGNS_DIR / f"{slug}.json"
    if not config_path.exists():
        return None

    with open(config_path) as f:
        config = json.load(f)

    _cache[slug] = config
    return config


def get_campaign_or_default(slug: str) -> dict[str, Any]:
    """Load a campaign configuration, falling back to defaults.

    Args:
        slug: Campaign identifier.

    Returns:
        Campaign config dict (guaranteed non-None).
    """
    config = get_campaign(slug)
    if config is not None:
        return config

    return {
        "slug": slug,
        "meta": {
            "title": "Arthur Agrelli",
            "description": "Inscreva-se agora",
        },
        "form": {
            "button_text": "Quero me inscrever!",
            "button_color": "bg-indigo-600",
            "loading_text": "Enviando...",
            "thank_you_url": f"/obrigado/{slug}/",
        },
        "headline": {
            "parts": [
                {"text": "Inscreva-se", "type": "normal"},
                {"text": " agora", "type": "highlight"},
            ],
        },
        "badges": [],
        "trust_badge": {
            "enabled": True,
            "text": "Suas informacoes estao seguras",
            "icon": "shield",
        },
        "social_proof": {
            "enabled": False,
        },
        "n8n": {
            "webhook_url": "",
            "launch_code": "",
            "list_id": "",
            "form_id": "",
            "form_name": "",
        },
    }
