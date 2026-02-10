"""
Identity URL configuration.
"""

from django.urls import path

from . import views

app_name = "identity"

urlpatterns = [
    # Auth pages
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
    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # Profile & Settings
    path("settings/", views.settings_view, name="settings"),
    path("settings/profile/", views.profile_view, name="profile"),
    path("settings/security/", views.settings_security_view, name="settings-security"),
    # Onboarding (Phase 4)
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path(
        "onboarding/verify-email/",
        views.onboarding_verify_email_view,
        name="onboarding-verify-email",
    ),
    path(
        "onboarding/resend-verification/",
        views.resend_verification_view,
        name="resend-verification",
    ),
    path("onboarding/legal/", views.onboarding_legal_view, name="onboarding-legal"),
    path(
        "onboarding/profile-completion/",
        views.onboarding_profile_completion_view,
        name="onboarding-profile-completion",
    ),
    path(
        "onboarding/plan-selection/",
        views.onboarding_plan_selection_view,
        name="onboarding-plan-selection",
    ),
]

# Shortcut for dashboard as home
urlpatterns += [
    path("", views.dashboard_view, name="home"),
]
