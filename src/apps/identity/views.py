"""
Identity views using Inertia.js.

Refactored to use service layer for business logic.
Views are thin controllers that delegate to AuthService and RegistrationService.

Data access: All views use request.data (provided by InertiaJsonParserMiddleware)
which works uniformly with both JSON and form-encoded requests.
Do NOT use request.POST directly — use request.data for consistency.
"""

from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from core.inertia import inertia_render, flash_success, flash_error
from .forms import ProfileForm
from .services import AuthService, RegistrationService


def _is_truthy(value) -> bool:
    """Parse boolean-like values from form data.

    HeroUI Checkbox sends boolean ``True``/``False``.  With ``forceFormData: true``
    Inertia serialises them as the strings ``"true"``/``"false"``.  Standard HTML
    checkboxes send ``"on"`` when checked and omit the field when unchecked.
    This helper normalises all those variants.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "on", "1", "yes")
    return bool(value)


def login_view(request):
    """Login page."""
    if request.user.is_authenticated:
        return redirect("identity:dashboard")

    if request.method == "POST":
        email = request.data.get("username", "")
        password = request.data.get("password", "")
        remember_me = _is_truthy(request.data.get("remember_me"))

        result = AuthService.login(email, password, request, remember_me)

        if result.success:
            flash_success(request, result.message)
            return redirect(result.redirect_url or "identity:dashboard")

        # Check if the error is about email verification
        needs_verification = "verify your email" in result.message.lower()

        return inertia_render(
            request,
            "Auth/Login",
            {
                "errors": result.errors,
                "needs_verification": needs_verification,
                "verification_email": email if needs_verification else None,
            },
        )

    return inertia_render(request, "Auth/Login")


def auth_verify_email_view(request):
    """
    Standalone email verification page (accessible without login).

    Two-step flow:
    1. GET or POST with 'action=send': User enters email → sends verification code
    2. POST with 'action=verify': User enters 6-digit OTP → verifies email

    After successful verification, redirects to login.
    """
    if request.user.is_authenticated:
        return redirect("identity:dashboard")

    if request.method == "POST":
        action = request.data.get("action", "send")
        email = request.data.get("email", "").lower().strip()

        if action == "send":
            # Step 1: Send verification code
            if not email:
                return inertia_render(
                    request,
                    "Auth/VerifyEmail",
                    {"step": "email", "errors": {"email": ["Email is required."]}},
                )

            success, message = RegistrationService.resend_verification_email(email)

            if success:
                flash_success(request, message)
            else:
                flash_error(request, message)

            return inertia_render(
                request,
                "Auth/VerifyEmail",
                {
                    "step": "code",
                    "email": email,
                },
            )

        elif action == "verify":
            # Step 2: Verify the OTP code
            code = request.data.get("verification_code", "")
            success, message, user = RegistrationService.verify_email(code)

            if success:
                flash_success(request, "Email verified! You can now log in.")
                return redirect("identity:login")

            return inertia_render(
                request,
                "Auth/VerifyEmail",
                {
                    "step": "code",
                    "email": email,
                    "errors": {"verification_code": [message]},
                },
            )

    # GET: show email form, optionally pre-filled
    email = request.GET.get("email", "")
    return inertia_render(
        request,
        "Auth/VerifyEmail",
        {
            "step": "email",
            "email": email,
        },
    )


def register_view(request):
    """Registration page."""
    if request.user.is_authenticated:
        return redirect("identity:dashboard")

    if request.method == "POST":
        email = request.data.get("email", "")
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        result = RegistrationService.register(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if result.success:
            flash_success(request, result.message)
            return redirect("identity:login")

        return inertia_render(
            request,
            "Auth/Register",
            {
                "errors": result.errors,
            },
        )

    return inertia_render(request, "Auth/Register")


@require_http_methods(["POST"])
def logout_view(request):
    """Logout action."""
    AuthService.logout(request)
    flash_success(request, "You have been logged out.")
    return redirect("identity:login")


def forgot_password_view(request):
    """Forgot password page."""
    if request.user.is_authenticated:
        return redirect("identity:dashboard")

    if request.method == "POST":
        email = request.data.get("email", "").lower().strip()
        result = AuthService.reset_password_request(email)
        flash_success(request, result["message"])
        return redirect("identity:login")

    return inertia_render(request, "Auth/ForgotPassword")


def reset_password_view(request, token):
    """
    Reset password page.

    GET: Show the password reset form with the token pre-filled.
    POST: Confirm the password reset with the verification code and new password.
    """
    if request.user.is_authenticated:
        return redirect("identity:dashboard")

    if request.method == "POST":
        verification_code = request.data.get("verification_code", token)
        new_password = request.data.get("new_password", "")

        result = AuthService.reset_password_confirm(
            verification_code=verification_code,
            new_password=new_password,
        )

        if result.success:
            flash_success(request, result.message)
            return redirect("identity:login")

        return inertia_render(
            request,
            "Auth/ResetPassword",
            {
                "token": token,
                "errors": result.errors,
            },
        )

    return inertia_render(
        request,
        "Auth/ResetPassword",
        {
            "token": token,
        },
    )


@login_required
def settings_security_view(request):
    """
    Security settings page for changing password.

    GET: Show the security settings form.
    POST: Change the user's password.
    """
    user = request.user

    if request.method == "POST":
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        result = AuthService.change_password(user, old_password, new_password)

        if result.success:
            # Re-login to update session hash after password change
            django_login(request, user)
            flash_success(request, result.message)
            return redirect("identity:settings-security")

        return inertia_render(
            request,
            "Settings/Security",
            {
                "user": user.to_dict(),
                "errors": result.errors,
            },
        )

    return inertia_render(
        request,
        "Settings/Security",
        {
            "user": user.to_dict(),
        },
    )


# =========================================
# Existing views (unchanged for Phase 7)
# =========================================


@login_required
def dashboard_view(request):
    """Main dashboard with real analytics data."""
    from apps.ads.services import AnalyticsService
    from apps.notifications.models import Notification

    analytics = AnalyticsService.get_dashboard_data()
    unread_notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    return inertia_render(
        request,
        "Dashboard/Index",
        {
            "user": request.user.to_dict(),
            "analytics": analytics,
            "unread_notifications": unread_notifications,
        },
    )


@login_required
def delinquent_view(request):
    """Standalone page shown when a user's subscription is delinquent."""
    if not request.user.is_delinquent:
        return redirect("identity:dashboard")

    message = request.GET.get("message") or None
    return inertia_render(
        request,
        "Delinquent",
        {
            "message": message,
        },
    )


@login_required
def profile_view(request):
    """User profile page."""
    user = request.user
    profile = getattr(user, "profile", None)

    if request.method == "POST":
        form = ProfileForm(request.data, request.FILES, instance=profile, user=user)
        if form.is_valid():
            form.save()
            flash_success(request, "Profile updated successfully!")
            return redirect("identity:profile")
        else:
            return inertia_render(
                request,
                "Settings/Profile",
                {
                    "user": user.to_dict(),
                    "profile": profile.to_dict() if profile else None,
                    "errors": form.errors,
                },
            )

    return inertia_render(
        request,
        "Settings/Profile",
        {
            "user": user.to_dict(),
            "profile": profile.to_dict() if profile else None,
        },
    )


@login_required
def settings_view(request):
    """User settings page."""
    return inertia_render(
        request,
        "Settings/Index",
        {
            "user": request.user.to_dict(),
        },
    )


# =========================================
# Onboarding views (Phase 4)
# =========================================


@login_required
def onboarding_view(request):
    """Route to the correct onboarding step."""
    from apps.identity.services import SetupStatusService

    status = SetupStatusService.get_setup_status(request.user)
    if status.is_complete:
        return redirect("identity:dashboard")
    return redirect(status.redirect_url)


@login_required
def onboarding_verify_email_view(request):
    """Email verification via 6-digit OTP."""
    from apps.identity.services import RegistrationService, SetupStatusService

    if request.method == "POST":
        code = request.data.get("verification_code", "")
        success, message, user = RegistrationService.verify_email(code)
        if success:
            SetupStatusService.complete_email_verification(request.user)
            flash_success(request, message)
            return redirect("identity:onboarding")
        return inertia_render(
            request,
            "Onboarding/VerifyEmail",
            {
                "email": request.user.email,
                "errors": {"verification_code": [message]},
            },
        )

    return inertia_render(
        request,
        "Onboarding/VerifyEmail",
        {
            "email": request.user.email,
        },
    )


@login_required
@require_http_methods(["POST"])
def resend_verification_view(request):
    """Resend verification email."""
    from apps.identity.services import RegistrationService

    success, message = RegistrationService.resend_verification_email(request.user.email)
    if success:
        flash_success(request, message)
    else:
        flash_error(request, message)
    return redirect("identity:onboarding-verify-email")


@login_required
def onboarding_legal_view(request):
    """Terms of use + privacy policy acceptance."""
    from apps.identity.services import SetupStatusService

    if request.method == "POST":
        agreed_terms = _is_truthy(request.data.get("agreed_to_terms"))
        agreed_privacy = _is_truthy(request.data.get("agreed_to_privacy"))
        agreed_marketing = _is_truthy(request.data.get("agreed_to_marketing"))

        if not agreed_terms or not agreed_privacy:
            return inertia_render(
                request,
                "Onboarding/Legal",
                {
                    "errors": {
                        "terms": ["You must accept the terms and privacy policy."]
                    },
                },
            )

        result = SetupStatusService.complete_legal_agreements(
            request.user, agreed_terms, agreed_privacy, agreed_marketing
        )

        if result.success:
            flash_success(request, result.message)
            return redirect("identity:onboarding")

        return inertia_render(
            request,
            "Onboarding/Legal",
            {"errors": {"terms": [result.message]}},
        )

    return inertia_render(request, "Onboarding/Legal")


@login_required
def onboarding_profile_completion_view(request):
    """Profile completion form."""
    from apps.identity.services import SetupStatusService

    if request.method == "POST":
        profile_data = {
            "phone": request.data.get("phone", ""),
            "first_name": request.data.get("first_name", ""),
            "last_name": request.data.get("last_name", ""),
            "company": request.data.get("company", ""),
            "bio": request.data.get("bio", ""),
        }

        result = SetupStatusService.complete_profile(request.user, profile_data)

        if result.success:
            flash_success(request, result.message)
            return redirect("identity:onboarding")

        return inertia_render(
            request,
            "Onboarding/ProfileCompletion",
            {
                "errors": {"profile": [result.message]},
                "profile_data": profile_data,
            },
        )

    profile = getattr(request.user, "profile", None)
    return inertia_render(
        request,
        "Onboarding/ProfileCompletion",
        {
            "profile_data": {
                "phone": profile.phone if profile else "",
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "company": "",
                "bio": profile.bio if profile else "",
            }
        },
    )


@login_required
def onboarding_plan_selection_view(request):
    """Plan selection."""
    from apps.identity.services import SetupStatusService

    if request.method == "POST":
        plan = request.data.get("plan", "free")
        result = SetupStatusService.complete_plan_selection(request.user, plan)

        if result.success:
            flash_success(request, result.message)
            return redirect("identity:dashboard")

        return inertia_render(
            request,
            "Onboarding/PlanSelection",
            {"errors": {"plan": [result.message]}},
        )

    return inertia_render(
        request,
        "Onboarding/PlanSelection",
        {
            "plans": [
                {
                    "id": "free",
                    "name": "Free",
                    "price": 0,
                    "features": [
                        "5 Contacts",
                        "1 User",
                        "Basic Reports",
                    ],
                },
                {
                    "id": "basic",
                    "name": "Basic",
                    "price": 49,
                    "features": [
                        "100 Contacts",
                        "5 Users",
                        "Advanced Reports",
                        "Email Support",
                    ],
                },
                {
                    "id": "premium",
                    "name": "Premium",
                    "price": 149,
                    "features": [
                        "Unlimited Contacts",
                        "Unlimited Users",
                        "Custom Reports",
                        "Priority Support",
                        "API Access",
                    ],
                },
            ],
        },
    )
