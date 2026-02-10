"""
Identity domain models.

Contains User and Profile models for authentication and user management.
Uses mixin architecture from core.shared for DRY code.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models, transaction
from django.utils import timezone

from core.shared.models import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    PublicIDMixin,
    MetadataMixin,
)


class UserManager(BaseUserManager):
    """
    Custom manager for User model.

    Inherits from BaseUserManager to ensure Django auth compatibility
    (provides get_by_natural_key, etc.).
    """

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def normalize_email(self, email):
        """Normalize email to lowercase."""
        return email.lower().strip() if email else email

    # Additional query methods
    def active(self):
        """Return only active, non-deleted users."""
        return self.filter(is_active=True, is_deleted=False)

    def verified(self):
        """Return only email-verified users."""
        return self.filter(email_verified=True, is_deleted=False)


class User(PublicIDMixin, SoftDeleteMixin, MetadataMixin, AbstractUser):
    """
    Custom User model using email as the primary identifier.

    Uses mixins for:
    - PublicIDMixin: Stripe-like public IDs (usr_xxxx)
    - SoftDeleteMixin: Soft delete support
    - MetadataMixin: Flexible JSON metadata

    Note: Does not use TimestampMixin because AbstractUser already has date_joined.
    """

    PUBLIC_ID_PREFIX = "usr"

    # Remove username, use email instead
    username = None
    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name="Email address",
    )

    # User status for employees
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        PENDING = "pending", "Pending Verification"
        SUSPENDED = "suspended", "Suspended"
        LOCKED = "locked", "Locked"

    # Setup/onboarding status
    class SetupStatus(models.TextChoices):
        INCOMPLETE = "incomplete", "Incomplete"
        BASIC = "basic", "Basic Setup"
        COMPLETE = "complete", "Complete"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # MFA support
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)

    # Setup/onboarding status
    setup_status = models.CharField(
        max_length=20,
        choices=SetupStatus.choices,
        default=SetupStatus.INCOMPLETE,
        db_index=True,
    )

    # Security tracking
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default="America/Sao_Paulo")
    language = models.CharField(max_length=10, default="pt-br")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(
                fields=["email_verified", "is_active"],
                name="idx_user_verified_active",
            ),
            models.Index(
                fields=["status", "is_deleted"],
                name="idx_user_status",
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def is_delinquent(self) -> bool:
        """
        Check if user has delinquent billing status.
        Returns False for now - will be implemented with billing integration.
        """
        return False

    def get_full_name(self):
        """Return first_name + last_name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email.split("@")[0]

    def get_short_name(self):
        """Return first_name or email prefix."""
        return self.first_name or self.email.split("@")[0]

    def verify_email(self):
        """Mark email as verified."""
        with transaction.atomic():
            self.email_verified = True
            self.email_verified_at = timezone.now()
            if self.status == self.Status.PENDING:
                self.status = self.Status.ACTIVE
            self.save(update_fields=["email_verified", "email_verified_at", "status"])

    def lock_account(self, reason: str = ""):
        """Lock the user account."""
        self.status = self.Status.LOCKED
        self.set_metadata("lock_reason", reason)
        self.set_metadata("locked_at", timezone.now().isoformat())
        self.save(update_fields=["status", "metadata"])

    def unlock_account(self):
        """Unlock the user account."""
        self.status = self.Status.ACTIVE
        self.failed_login_attempts = 0
        self.remove_metadata("lock_reason")
        self.remove_metadata("locked_at")
        self.save(update_fields=["status", "failed_login_attempts", "metadata"])

    def record_login(self, ip_address: str):
        """Record successful login."""
        self.last_login_ip = ip_address
        self.last_login_at = timezone.now()
        self.failed_login_attempts = 0
        self.save(
            update_fields=["last_login_ip", "last_login_at", "failed_login_attempts"]
        )

    def record_failed_login(self):
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account("Too many failed login attempts")
        else:
            self.save(update_fields=["failed_login_attempts"])

    def to_dict(self) -> dict:
        """Serialize user for Inertia props."""
        return {
            "id": self.public_id,
            "email": self.email,
            "name": self.get_full_name(),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "status": self.status,
            "setup_status": self.setup_status,
            "email_verified": self.email_verified,
            "mfa_enabled": self.mfa_enabled,
            "timezone": self.timezone,
            "language": self.language,
            "is_staff": self.is_staff,
            "is_delinquent": self.is_delinquent,
            "date_joined": self.date_joined.isoformat() if self.date_joined else None,
        }


class Profile(BaseModel):
    """
    Extended user profile for employee information.

    Inherits from BaseModel which includes:
    - TimestampMixin (created_at, updated_at)
    - SoftDeleteMixin (is_deleted, deleted_at)
    - PublicIDMixin (public_id)
    - ActivatableMixin (is_active)
    - MetadataMixin (metadata)
    - VersionableMixin (version)

    Includes employee terms acceptance tracking for system access.
    """

    PUBLIC_ID_PREFIX = "prf"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Personal info
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    # Avatar
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        null=True,
        blank=True,
    )

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="BR")

    # Settings
    notification_preferences = models.JSONField(default=dict, blank=True)

    # =========================================
    # Employee Terms Acceptance
    # (Required before accessing the system)
    # =========================================
    agreed_to_terms = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Has accepted employee terms of use",
    )
    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When employee terms were accepted",
    )
    terms_version = models.CharField(
        max_length=20,
        blank=True,
        help_text="Version of terms accepted (e.g., '2026.02')",
    )
    terms_accepted_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when terms were accepted",
    )

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(
                fields=["agreed_to_terms", "is_active"],
                name="idx_profile_terms_active",
            ),
        ]

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def can_access_system(self) -> bool:
        """
        Check if employee can access the system.
        Requires terms acceptance.
        """
        return self.agreed_to_terms and self.is_active and not self.is_deleted

    def accept_terms(self, ip_address: str = None, version: str = "2026.02"):
        """
        Mark employee terms as accepted.

        Args:
            ip_address: IP address of acceptance (for audit trail)
            version: Version of terms being accepted
        """
        with transaction.atomic():
            self.agreed_to_terms = True
            self.terms_accepted_at = timezone.now()
            self.terms_version = version
            if ip_address:
                self.terms_accepted_ip = ip_address
            self.save(
                update_fields=[
                    "agreed_to_terms",
                    "terms_accepted_at",
                    "terms_version",
                    "terms_accepted_ip",
                ]
            )

    def revoke_terms(self):
        """
        Revoke terms acceptance (e.g., when new terms version is released).
        Employee will need to accept new terms.
        """
        with transaction.atomic():
            self.agreed_to_terms = False
            # Keep historical data in metadata for audit
            if self.terms_accepted_at:
                self.update_metadata(
                    {
                        "previous_terms_accepted_at": self.terms_accepted_at.isoformat(),
                        "previous_terms_version": self.terms_version,
                        "terms_revoked_at": timezone.now().isoformat(),
                    }
                )
            self.terms_accepted_at = None
            self.terms_version = ""
            self.terms_accepted_ip = None
            self.save(
                update_fields=[
                    "agreed_to_terms",
                    "terms_accepted_at",
                    "terms_version",
                    "terms_accepted_ip",
                    "metadata",
                ]
            )

    def to_dict(self) -> dict:
        """Serialize profile for Inertia props."""
        return {
            "id": self.public_id,
            "phone": self.phone,
            "bio": self.bio,
            "avatar_url": self.avatar.url if self.avatar else None,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "notification_preferences": self.notification_preferences,
            "agreed_to_terms": self.agreed_to_terms,
            "terms_accepted_at": self.terms_accepted_at.isoformat()
            if self.terms_accepted_at
            else None,
            "terms_version": self.terms_version,
            "can_access_system": self.can_access_system,
        }
