"""
Celery tasks for contact email processing.

Async processing for:
- New email processing + fingerprint association
- Email verification (send + confirm)
- Bounce handling
- Confidence score update after email events

Ported from legacy contact/tasks.py (email-related tasks).
"""

from __future__ import annotations

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


@shared_task(
    name="contact_email.process_new_email",
    queue="contact_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def process_new_email(email_value: str, original_value: str | None = None) -> dict:
    """
    Process a new email: create/get, associate with fingerprints, trigger verification.

    Args:
        email_value: The email address value.
        original_value: Original user input before normalization.
    """
    try:
        from apps.contacts.email.services.email_service import EmailService

        service = EmailService()
        email_obj, created = service.get_or_create_email(email_value)

        if created:
            # Chain: associate with fingerprints, then verify
            associate_email_with_fingerprints.delay(email_obj.id)
            verify_email.delay(email_obj.id)

        logger.info("Processed email %s (created=%s)", email_obj.value, created)
        return {
            "status": "success",
            "email_id": email_obj.public_id,
            "created": created,
        }

    except Exception as e:
        logger.exception("Error processing email %s: %s", email_value, str(e))
        raise


@shared_task(
    name="contact_email.associate_with_fingerprints",
    queue="contact_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def associate_email_with_fingerprints(email_id: int) -> dict:
    """
    Associate an email with existing fingerprints that have used it in events.

    Searches FingerprintEvent.user_data and event_data for matching email.

    Args:
        email_id: Primary key of the ContactEmail.
    """
    try:
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.fingerprint.models import (
            FingerprintIdentity,
            FingerprintEvent,
            FingerprintContact,
        )

        email = ContactEmail.objects.filter(id=email_id).first()
        if not email:
            return {"status": "error", "message": f"Email {email_id} not found"}

        # Find fingerprints where this email appears in event data
        fp_ids_user = (
            FingerprintEvent.objects.filter(user_data__contains={"email": email.value})
            .values_list("fingerprint_id", flat=True)
            .distinct()
        )

        fp_ids_event = (
            FingerprintEvent.objects.filter(event_data__contains={"email": email.value})
            .values_list("fingerprint_id", flat=True)
            .distinct()
        )

        fp_ids = set(fp_ids_user) | set(fp_ids_event)
        fingerprints = FingerprintIdentity.objects.filter(id__in=fp_ids)

        associated = 0
        with transaction.atomic():
            for fp in fingerprints:
                FingerprintContact.objects.get_or_create(
                    fingerprint=fp,
                    content_type=ContentType.objects.get_for_model(ContactEmail),
                    object_id=email.id,
                    defaults={
                        "verification_status": "unverified",
                        "first_seen": timezone.now(),
                        "last_seen": timezone.now(),
                    },
                )
                associated += 1

                # Link email to fingerprint's identity if not yet linked
                if not email.identity and fp.identity:
                    email.identity = fp.identity
                    email.save(update_fields=["identity", "updated_at"])

        logger.info("Associated email %s with %d fingerprints", email.value, associated)
        return {
            "status": "success",
            "email_id": email.public_id,
            "fingerprints_associated": associated,
        }

    except Exception as e:
        logger.exception(
            "Error associating email %d with fingerprints: %s", email_id, str(e)
        )
        raise


@shared_task(
    name="contact_email.verify",
    queue="contact_verification",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 300},
    acks_late=True,
)
def verify_email(email_id: int) -> dict:
    """
    Send verification email and trigger confidence recalculation.

    Args:
        email_id: Primary key of the ContactEmail.
    """
    try:
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.email.services.verification_service import (
            VerificationService,
        )

        email = ContactEmail.objects.filter(id=email_id).first()
        if not email:
            return {"status": "error", "message": f"Email {email_id} not found"}

        result = VerificationService.send_email_verification(email)

        # Recalculate identity confidence
        if email.identity_id:
            from apps.contacts.identity.tasks import calculate_confidence_score

            calculate_confidence_score.delay(email.identity_id)

        logger.info("Sent verification for email %s", email.value)
        return {
            "status": "success",
            "email_id": email.public_id,
            "verification_sent": True,
        }

    except Exception as e:
        logger.exception("Error verifying email %d: %s", email_id, str(e))
        raise


@shared_task(
    name="contact_email.confirm_verification",
    queue="contact_verification",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def confirm_email_verification(
    email_id: int,
    code: str | None = None,
    token: str | None = None,
) -> dict:
    """
    Confirm email verification with a code or token.

    Args:
        email_id: Primary key of the ContactEmail.
        code: 6-digit verification code.
        token: Verification token.
    """
    try:
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.email.services.verification_service import (
            VerificationService,
        )

        email = ContactEmail.objects.filter(id=email_id).first()
        if not email:
            return {"status": "error", "message": f"Email {email_id} not found"}

        if code:
            verified = VerificationService.verify_email_with_code(email, code)
        elif token:
            verified = VerificationService.verify_email_with_token(email, token)
        else:
            return {"status": "error", "message": "Code or token required"}

        # Recalculate identity confidence after verification
        if email.identity_id and verified:
            from apps.contacts.identity.tasks import calculate_confidence_score

            calculate_confidence_score.delay(email.identity_id)

        return {
            "status": "success" if verified else "error",
            "email_id": email.public_id,
            "verified": verified,
        }

    except Exception as e:
        logger.exception("Error confirming email %d: %s", email_id, str(e))
        raise


@shared_task(
    name="contact_email.handle_bounce",
    queue="contact_events",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def handle_email_bounce(email_id: int, bounce_data: dict) -> dict:
    """
    Process an email bounce event.

    Args:
        email_id: Primary key of the ContactEmail.
        bounce_data: Dict with bounce type, reason, timestamp, etc.
    """
    try:
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.email.services.email_service import EmailService

        email = ContactEmail.objects.filter(id=email_id).first()
        if not email:
            return {"status": "error", "message": f"Email {email_id} not found"}

        service = EmailService()
        updated_email = service.process_email_bounce(email, bounce_data)

        # Recalculate identity confidence after bounce
        if email.identity_id:
            from apps.contacts.identity.tasks import calculate_confidence_score

            calculate_confidence_score.delay(email.identity_id)

        logger.info("Processed bounce for email %s", email.value)
        return {
            "status": "success",
            "email_id": email.public_id,
            "bounce_processed": True,
        }

    except Exception as e:
        logger.exception("Error processing bounce for email %d: %s", email_id, str(e))
        raise
