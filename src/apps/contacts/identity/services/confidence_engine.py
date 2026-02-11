"""
Unified Confidence Scoring Engine.

Replaces 3 duplicated confidence formulas:
1. IdentityService.calculate_confidence_score (simple: base + verified counts)
2. ResolutionService.calculate_real_confidence_score (sophisticated: FP avg + bonuses - fraud)
3. ResolutionService.calculate_initial_confidence_score (basic: FP score + contact presence)

This engine provides a single, comprehensive scoring algorithm with two modes:
- `calculate()`: Full recalculation from DB relationships (used after events)
- `calculate_initial()`: Fast estimate for newly created identities (used during resolution)
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.contacts.identity.models import Identity

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """
    Single source of truth for identity confidence scoring.

    Scoring components:
    ┌─────────────────────────────────────┬────────┐
    │ Component                           │ Weight │
    ├─────────────────────────────────────┼────────┤
    │ Base (minimum for any identity)     │  0.10  │
    │ FingerprintJS avg confidence        │  0-0.30│
    │ Verified email (each, max 2)        │ +0.15  │
    │ Unverified email (each, max 2)      │ +0.05  │
    │ Verified phone (each, max 2)        │ +0.20  │
    │ Unverified phone (each, max 2)      │ +0.10  │
    │ Cross-device bonus (unique types)   │ +0.05/d│
    │ Penalty: incognito browsing         │ -0.10  │
    │ Penalty: VPN/proxy (high accuracy)  │ -0.15  │
    │ Penalty: bounced email              │ -0.20  │
    │ Penalty: DNC phone                  │ -0.15  │
    └─────────────────────────────────────┴────────┘

    Final score is clamped to [0.0, 1.0].
    """

    # Weight constants
    BASE_SCORE = 0.10

    # Fingerprint
    FP_WEIGHT = 0.30  # Max contribution from FP confidence average

    # Email
    VERIFIED_EMAIL_BONUS = 0.15
    UNVERIFIED_EMAIL_BONUS = 0.05
    MAX_EMAIL_CONTRIBUTIONS = 2

    # Phone
    VERIFIED_PHONE_BONUS = 0.20
    UNVERIFIED_PHONE_BONUS = 0.10
    MAX_PHONE_CONTRIBUTIONS = 2

    # Cross-device
    CROSS_DEVICE_BONUS = 0.05
    MAX_CROSS_DEVICE_BONUS = 0.15

    # Fraud penalties
    INCOGNITO_PENALTY = 0.10
    VPN_PENALTY = 0.15
    VPN_ACCURACY_THRESHOLD = 1000  # accuracy_radius in meters

    # Contact quality penalties
    BOUNCED_EMAIL_PENALTY = 0.20
    DNC_PHONE_PENALTY = 0.15

    @classmethod
    def calculate(cls, identity: "Identity") -> float:
        """
        Full confidence recalculation from DB relationships.

        Queries all emails, phones, and fingerprints for the identity
        and computes a comprehensive score. Saves the result.

        Args:
            identity: The Identity to score.

        Returns:
            The computed confidence score (0.0 - 1.0).
        """
        from apps.contacts.identity.models import IdentityHistory

        score = cls.BASE_SCORE
        components = {"base": cls.BASE_SCORE}

        # ── Fingerprint component ─────────────────────────────────────
        fingerprints = list(identity.fingerprints.all())
        if fingerprints:
            fp_avg = sum(fp.confidence_score for fp in fingerprints) / len(fingerprints)
            fp_contribution = fp_avg * cls.FP_WEIGHT
            score += fp_contribution
            components["fingerprint_avg"] = round(fp_avg, 3)
            components["fingerprint_contribution"] = round(fp_contribution, 3)

            # Cross-device bonus
            device_types = set(fp.device_type for fp in fingerprints if fp.device_type)
            cross_bonus = min(
                len(device_types) * cls.CROSS_DEVICE_BONUS, cls.MAX_CROSS_DEVICE_BONUS
            )
            score += cross_bonus
            components["cross_device_bonus"] = round(cross_bonus, 3)

            # Fraud penalties
            fraud_penalty = 0.0
            for fp in fingerprints:
                if fp.browser_info.get("incognito", False):
                    fraud_penalty += cls.INCOGNITO_PENALTY
                accuracy = fp.geo_info.get("accuracy_radius", 0)
                if accuracy and accuracy > cls.VPN_ACCURACY_THRESHOLD:
                    fraud_penalty += cls.VPN_PENALTY

            if fraud_penalty > 0:
                score -= fraud_penalty
                components["fraud_penalty"] = round(-fraud_penalty, 3)
        else:
            components["fingerprint_contribution"] = 0.0

        # ── Email component ───────────────────────────────────────────
        emails = list(identity.email_contacts.all())
        email_bonus = 0.0
        bounced_penalty = 0.0
        for i, email in enumerate(emails):
            if i >= cls.MAX_EMAIL_CONTRIBUTIONS:
                break
            if email.is_verified:
                email_bonus += cls.VERIFIED_EMAIL_BONUS
            else:
                email_bonus += cls.UNVERIFIED_EMAIL_BONUS

        # Check for bounced emails via lifecycle_status (P1.2 field)
        for email in emails:
            lifecycle = getattr(email, "lifecycle_status", None)
            if lifecycle and lifecycle in ("bounced_hard", "bounced_soft"):
                bounced_penalty += cls.BOUNCED_EMAIL_PENALTY

        score += email_bonus - bounced_penalty
        components["email_bonus"] = round(email_bonus, 3)
        if bounced_penalty > 0:
            components["bounced_email_penalty"] = round(-bounced_penalty, 3)

        # ── Phone component ───────────────────────────────────────────
        phones = list(identity.phone_contacts.all())
        phone_bonus = 0.0
        dnc_penalty = 0.0
        for i, phone in enumerate(phones):
            if i >= cls.MAX_PHONE_CONTRIBUTIONS:
                break
            if phone.is_verified:
                phone_bonus += cls.VERIFIED_PHONE_BONUS
            else:
                phone_bonus += cls.UNVERIFIED_PHONE_BONUS

        # DNC penalty
        for phone in phones:
            if phone.is_dnc:
                dnc_penalty += cls.DNC_PHONE_PENALTY

        score += phone_bonus - dnc_penalty
        components["phone_bonus"] = round(phone_bonus, 3)
        if dnc_penalty > 0:
            components["dnc_phone_penalty"] = round(-dnc_penalty, 3)

        # ── Clamp and save ────────────────────────────────────────────
        final_score = max(0.0, min(score, 1.0))
        components["final_score"] = round(final_score, 3)

        identity.confidence_score = final_score
        identity.save(update_fields=["confidence_score", "updated_at"])

        # Record in history
        IdentityHistory.objects.create(
            identity=identity,
            operation_type=IdentityHistory.CONFIDENCE_UPDATE,
            details={
                "score": round(final_score, 3),
                "components": components,
                "emails_count": len(emails),
                "phones_count": len(phones),
                "fingerprints_count": len(fingerprints),
            },
        )

        logger.info(
            "Confidence score for %s: %.3f (emails=%d, phones=%d, fps=%d)",
            identity.public_id,
            final_score,
            len(emails),
            len(phones),
            len(fingerprints),
        )

        return final_score

    @classmethod
    def calculate_initial(
        cls,
        fingerprint_confidence: float,
        has_email: bool = False,
        has_phone: bool = False,
    ) -> float:
        """
        Fast confidence estimate for a newly created identity.

        Used during resolution when we don't have full relationship data yet.
        Does NOT save to DB.

        Args:
            fingerprint_confidence: FingerprintJS confidence score (0.0-1.0).
            has_email: Whether contact data includes an email.
            has_phone: Whether contact data includes a phone.

        Returns:
            Estimated confidence score (0.0 - 1.0).
        """
        score = cls.BASE_SCORE

        # FP contribution
        fp_score = (fingerprint_confidence or 0.3) * cls.FP_WEIGHT
        score += fp_score

        # Contact presence bonuses (unverified since they're new)
        if has_email:
            score += cls.UNVERIFIED_EMAIL_BONUS
        if has_phone:
            score += cls.UNVERIFIED_PHONE_BONUS

        return max(0.0, min(score, 1.0))
