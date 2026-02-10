"""
Employee terms acceptance decorator.
"""
import functools
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages


def require_terms_accepted(
    redirect_url: str = "/terms/accept/",
    message: Optional[str] = None
):
    """
    Decorator to require employee terms acceptance before accessing a view.

    Usage:
        @require_terms_accepted()
        def dashboard(request):
            ...

        @require_terms_accepted(redirect_url="/custom/terms/")
        def protected_view(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return redirect("login")

            # Check if user has profile and accepted terms
            try:
                profile = request.user.profile
                if not profile.can_access_system:
                    if message:
                        messages.warning(request, message)
                    else:
                        messages.warning(
                            request,
                            "Você precisa aceitar os termos de uso para acessar o sistema."
                        )
                    return redirect(redirect_url)
            except AttributeError:
                # User has no profile - should not happen in normal flow
                messages.error(request, "Perfil não encontrado. Contate o administrador.")
                return redirect(redirect_url)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RequireTermsMixin:
    """
    Mixin for class-based views to require terms acceptance.

    Usage:
        class DashboardView(RequireTermsMixin, View):
            terms_redirect_url = "/terms/accept/"

            def get(self, request):
                ...
    """
    terms_redirect_url: str = "/terms/accept/"
    terms_required_message: str = "Você precisa aceitar os termos de uso para acessar o sistema."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        try:
            if not request.user.profile.can_access_system:
                messages.warning(request, self.terms_required_message)
                return redirect(self.terms_redirect_url)
        except AttributeError:
            messages.error(request, "Perfil não encontrado.")
            return redirect(self.terms_redirect_url)

        return super().dispatch(request, *args, **kwargs)
