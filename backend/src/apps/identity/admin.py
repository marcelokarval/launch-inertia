"""
Identity admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin

from .models import User, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Custom User admin."""

    list_display = [
        "email",
        "first_name",
        "last_name",
        "status",
        "email_verified",
        "is_staff",
        "date_joined",
    ]
    list_filter = [
        "status",
        "email_verified",
        "is_staff",
        "is_superuser",
        "mfa_enabled",
        "date_joined",
    ]
    search_fields = ["email", "first_name", "last_name", "public_id"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password", "public_id")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Status", {"fields": ("status", "email_verified", "email_verified_at")}),
        ("Security", {"fields": ("mfa_enabled", "failed_login_attempts", "last_login_ip", "last_login_at")}),
        ("Preferences", {"fields": ("timezone", "language")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    readonly_fields = ["public_id", "email_verified_at", "last_login_ip", "last_login_at", "date_joined"]


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    """Profile admin."""

    list_display = ["user", "phone", "city", "country", "created_at"]
    list_filter = ["country", "created_at"]
    search_fields = ["user__email", "phone", "city"]
    readonly_fields = ["public_id", "created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("user", "public_id")}),
        ("Personal", {"fields": ("phone", "bio", "avatar")}),
        ("Address", {"fields": ("address_line1", "address_line2", "city", "state", "postal_code", "country")}),
        ("Preferences", {"fields": ("notification_preferences",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
