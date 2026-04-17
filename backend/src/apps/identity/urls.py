"""Identity URL configuration.

Split into auth (root level) and dashboard (under /app/).
"""

from django.urls import path

from . import views

app_name = "identity"

# ── Auth pages (pre-login, NOT under /app/) ──────────────────────
auth_urlpatterns = [
    path("auth/login/", views.login_view, name="login"),
    path("auth/register/", views.register_view, name="register"),
    path("auth/verify-email/", views.auth_verify_email_view, name="auth-verify-email"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/forgot-password/", views.forgot_password_view, name="forgot-password"),
    path(
        "auth/reset-password/<str:token>/",
        views.reset_password_view,
        name="reset-password",
    ),
]

# ── Dashboard pages (under /app/ via root urls.py) ───────────────
dashboard_urlpatterns = [
    # Dashboard home: /app/
    path("", views.dashboard_view, name="dashboard"),
    # Settings: /app/settings/
    path("settings/", views.settings_view, name="settings"),
    path("settings/profile/", views.profile_view, name="profile"),
    path("settings/security/", views.settings_security_view, name="settings-security"),
    # Delinquent: /app/delinquent/
    path("delinquent/", views.delinquent_view, name="delinquent"),
]

# Combined urlpatterns for backward compatibility with include()
# Root urls.py should use the specific lists instead.
urlpatterns = auth_urlpatterns + dashboard_urlpatterns
