"""
Setup status service for onboarding flow management.

Manages the multi-step onboarding process: email verification,
legal agreements, profile completion, and plan selection.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum

from django.db import transaction
from django.utils import timezone

from apps.identity.models import User, Profile

logger = logging.getLogger(__name__)


class SetupStage(str, Enum):
    """Stages of the onboarding process."""

    EMAIL_VERIFICATION = "email_verification"
    LEGAL_AGREEMENTS = "legal_agreements"
    PROFILE_COMPLETION = "profile_completion"
    PLAN_SELECTION = "plan_selection"


# Stage-to-URL mapping
STAGE_URLS = {
    SetupStage.EMAIL_VERIFICATION: "/onboarding/verify-email/",
    SetupStage.LEGAL_AGREEMENTS: "/onboarding/legal/",
    SetupStage.PROFILE_COMPLETION: "/onboarding/profile-completion/",
    SetupStage.PLAN_SELECTION: "/onboarding/plan-selection/",
}

# All stages in order
STAGES_ORDER = [
    SetupStage.EMAIL_VERIFICATION,
    SetupStage.LEGAL_AGREEMENTS,
    SetupStage.PROFILE_COMPLETION,
    SetupStage.PLAN_SELECTION,
]

PROGRESS_PER_STAGE = 25  # 25% per stage (4 stages = 100%)


@dataclass
class SetupStatus:
    """Current setup/onboarding status for a user."""

    current_stage: SetupStage | None
    completed_stages: list[SetupStage] = field(default_factory=list)
    progress_percentage: int = 0
    is_complete: bool = False
    redirect_url: str = "/onboarding/"  # Default; stages override with specific URLs

    def to_dict(self) -> dict:
        """Serialize for Inertia props."""
        return {
            "current_stage": self.current_stage.value if self.current_stage else None,
            "completed_stages": [s.value for s in self.completed_stages],
            "progress_percentage": self.progress_percentage,
            "is_complete": self.is_complete,
            "redirect_url": self.redirect_url,
        }


@dataclass
class StageCompletionResult:
    """Result of completing a setup stage."""

    success: bool
    message: str
    next_stage: SetupStage | None = None
    progress_percentage: int = 0


class SetupStatusService:
    """
    Service for managing user onboarding/setup flow.

    All methods are static. No instance state.
    Handles stage progression, completion tracking, and redirects.
    """

    @staticmethod
    def get_setup_status(user: User) -> SetupStatus:
        """
        Determine the current setup status for a user.

        Checks stages in order:
        1. Email verified?
        2. Legal agreements accepted?
        3. Profile has required fields (phone, first_name, last_name)?
        4. Setup status == "complete"?

        Args:
            user: The user to check.

        Returns:
            SetupStatus with current stage and redirect URL.
        """
        completed_stages: list[SetupStage] = []

        # Stage 1: Email verification
        if not user.email_verified:
            return SetupStatus(
                current_stage=SetupStage.EMAIL_VERIFICATION,
                completed_stages=completed_stages,
                progress_percentage=len(completed_stages) * PROGRESS_PER_STAGE,
                is_complete=False,
                redirect_url=STAGE_URLS[SetupStage.EMAIL_VERIFICATION],
            )
        completed_stages.append(SetupStage.EMAIL_VERIFICATION)

        # Stage 2: Legal agreements
        profile = SetupStatusService._get_or_create_profile(user)
        if not profile.agreed_to_terms:
            return SetupStatus(
                current_stage=SetupStage.LEGAL_AGREEMENTS,
                completed_stages=completed_stages,
                progress_percentage=len(completed_stages) * PROGRESS_PER_STAGE,
                is_complete=False,
                redirect_url=STAGE_URLS[SetupStage.LEGAL_AGREEMENTS],
            )
        completed_stages.append(SetupStage.LEGAL_AGREEMENTS)

        # Stage 3: Profile completion (requires phone, first_name, last_name)
        has_required_fields = all(
            [
                user.first_name,
                user.last_name,
                profile.phone,
            ]
        )
        if not has_required_fields:
            return SetupStatus(
                current_stage=SetupStage.PROFILE_COMPLETION,
                completed_stages=completed_stages,
                progress_percentage=len(completed_stages) * PROGRESS_PER_STAGE,
                is_complete=False,
                redirect_url=STAGE_URLS[SetupStage.PROFILE_COMPLETION],
            )
        completed_stages.append(SetupStage.PROFILE_COMPLETION)

        # Stage 4: Plan selection (setup_status must be "complete")
        if user.setup_status != User.SetupStatus.COMPLETE:
            return SetupStatus(
                current_stage=SetupStage.PLAN_SELECTION,
                completed_stages=completed_stages,
                progress_percentage=len(completed_stages) * PROGRESS_PER_STAGE,
                is_complete=False,
                redirect_url=STAGE_URLS[SetupStage.PLAN_SELECTION],
            )
        completed_stages.append(SetupStage.PLAN_SELECTION)

        # All stages complete
        return SetupStatus(
            current_stage=None,
            completed_stages=completed_stages,
            progress_percentage=100,
            is_complete=True,
            redirect_url="/app/",
        )

    @staticmethod
    @transaction.atomic
    def complete_email_verification(user: User) -> StageCompletionResult:
        """
        Mark email verification stage as complete.

        Note: The actual email verification (OTP check) is handled by
        RegistrationService.verify_email(). This method is called after
        that succeeds to progress the onboarding flow.

        Args:
            user: The user who verified their email.

        Returns:
            StageCompletionResult with next stage info.
        """
        if not user.email_verified:
            return StageCompletionResult(
                success=False,
                message="Email has not been verified yet.",
            )

        logger.info("Email verification stage completed for user: %s", user.email)

        return StageCompletionResult(
            success=True,
            message="Email verified successfully!",
            next_stage=SetupStage.LEGAL_AGREEMENTS,
            progress_percentage=PROGRESS_PER_STAGE,
        )

    @staticmethod
    @transaction.atomic
    def complete_legal_agreements(
        user: User,
        agreed_terms: bool,
        agreed_privacy: bool,
        agreed_marketing: bool = False,
    ) -> StageCompletionResult:
        """
        Record legal agreement acceptance.

        Args:
            user: The user accepting terms.
            agreed_terms: Whether user agreed to terms of use.
            agreed_privacy: Whether user agreed to privacy policy.
            agreed_marketing: Whether user opted into marketing emails.

        Returns:
            StageCompletionResult with next stage info.
        """
        if not agreed_terms or not agreed_privacy:
            return StageCompletionResult(
                success=False,
                message="You must accept both the Terms of Use and Privacy Policy.",
            )

        profile = SetupStatusService._get_or_create_profile(user)

        # Use the Profile model's accept_terms method
        profile.accept_terms(version="2026.02")

        # Store marketing preference in metadata
        profile.update_metadata(
            {
                "agreed_to_privacy": True,
                "agreed_to_privacy_at": timezone.now().isoformat(),
                "agreed_to_marketing": agreed_marketing,
                "agreed_to_marketing_at": timezone.now().isoformat()
                if agreed_marketing
                else None,
            }
        )

        logger.info("Legal agreements completed for user: %s", user.email)

        return StageCompletionResult(
            success=True,
            message="Terms accepted successfully!",
            next_stage=SetupStage.PROFILE_COMPLETION,
            progress_percentage=2 * PROGRESS_PER_STAGE,
        )

    @staticmethod
    @transaction.atomic
    def complete_profile(user: User, profile_data: dict) -> StageCompletionResult:
        """
        Complete the profile with required fields.

        Args:
            user: The user completing their profile.
            profile_data: Dict with keys: first_name, last_name, phone,
                          and optionally: company, bio.

        Returns:
            StageCompletionResult with next stage info.
        """
        first_name = profile_data.get("first_name", "").strip()
        last_name = profile_data.get("last_name", "").strip()
        phone = profile_data.get("phone", "").strip()

        # Validate required fields
        if not first_name or not last_name:
            return StageCompletionResult(
                success=False,
                message="First name and last name are required.",
            )

        if not phone:
            return StageCompletionResult(
                success=False,
                message="Phone number is required.",
            )

        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])

        # Update profile fields
        profile = SetupStatusService._get_or_create_profile(user)
        profile.phone = phone

        company = profile_data.get("company", "").strip()
        bio = profile_data.get("bio", "").strip()

        if company:
            profile.update_metadata({"company": company})
        if bio:
            profile.bio = bio

        profile.save(update_fields=["phone", "bio", "metadata"])

        logger.info("Profile completion stage completed for user: %s", user.email)

        return StageCompletionResult(
            success=True,
            message="Profile completed successfully!",
            next_stage=SetupStage.PLAN_SELECTION,
            progress_percentage=3 * PROGRESS_PER_STAGE,
        )

    @staticmethod
    @transaction.atomic
    def complete_plan_selection(user: User, plan: str) -> StageCompletionResult:
        """
        Complete plan selection and finish onboarding.

        Args:
            user: The user selecting a plan.
            plan: The plan ID (e.g., "free", "basic", "premium").

        Returns:
            StageCompletionResult with completion info.
        """
        valid_plans = {"free", "basic", "premium"}
        if plan not in valid_plans:
            return StageCompletionResult(
                success=False,
                message=f"Invalid plan. Choose from: {', '.join(valid_plans)}",
            )

        # Store selected plan in user metadata
        user.set_metadata("selected_plan", plan)
        user.set_metadata("plan_selected_at", timezone.now().isoformat())

        # Mark setup as complete
        user.setup_status = User.SetupStatus.COMPLETE
        user.save(update_fields=["setup_status", "metadata"])

        logger.info(
            "Plan selection completed for user %s: plan=%s",
            user.email,
            plan,
        )

        return StageCompletionResult(
            success=True,
            message="Setup complete! Welcome to Launch.",
            next_stage=None,
            progress_percentage=100,
        )

    @staticmethod
    def _get_or_create_profile(user: User) -> Profile:
        """Get or create a profile for the user."""
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            logger.info("Created missing profile for user: %s", user.email)
        return profile
