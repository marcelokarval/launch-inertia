"""
Landing page views.

All landing views use app="landing" to render via the landing.html template
and the landing Vite build.
"""

from django.http import HttpRequest, HttpResponse

from core.inertia.helpers import inertia_render


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
