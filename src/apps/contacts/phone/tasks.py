"""
Celery tasks for contact phone processing.

Async processing for:
- New phone processing + fingerprint association
- Phone verification (send + confirm)
- Confidence score update after phone events

Ported from legacy contact/tasks.py (phone-related tasks).
"""

from __future__ import annotations

import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


@shared_task(
    name="contact_phone.process_new_phone",
    queue="contact_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def process_new_phone(
    phone_value: str,
    original_value: str | None = None,
    country_code: str | None = None,
) -> dict:
    """
    Process a new phone: create/get, associate with fingerprints, trigger verification.

    Args:
        phone_value: The phone number value.
        original_value: Original user input before normalization.
        country_code: Country code (default: "55" for Brazil).
    """
    try:
        from apps.contacts.phone.services.phone_service import PhoneService

        service = PhoneService()
        phone_obj, created = service.get_or_create_phone(
            phone_value, country_code=country_code
        )

        if created:
            associate_phone_with_fingerprints.delay(phone_obj.id)
            verify_phone.delay(phone_obj.id)

        logger.info("Processed phone %s (created=%s)", phone_obj.value, created)
        return {
            "status": "success",
            "phone_id": phone_obj.public_id,
            "created": created,
        }

    except Exception as e:
        logger.exception("Error processing phone %s: %s", phone_value, str(e))
        raise


@shared_task(
    name="contact_phone.associate_with_fingerprints",
    queue="contact_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def associate_phone_with_fingerprints(phone_id: int) -> dict:
    """
    Associate a phone with existing fingerprints that have used it in events.

    Searches FingerprintEvent.user_data and event_data for matching phone.

    Args:
        phone_id: Primary key of the ContactPhone.
    """
    try:
        from apps.contacts.phone.models import ContactPhone
        from apps.contacts.fingerprint.models import (
            FingerprintIdentity,
            FingerprintEvent,
            FingerprintContact,
        )

        phone = ContactPhone.objects.filter(id=phone_id).first()
        if not phone:
            return {"status": "error", "message": f"Phone {phone_id} not found"}

        # Search across multiple field names
        fp_ids = set()
        for field_name in ["phone", "phone_number"]:
            fp_ids_user = (
                FingerprintEvent.objects.filter(
                    user_data__contains={field_name: phone.value}
                )
                .values_list("fingerprint_id", flat=True)
                .distinct()
            )
            fp_ids.update(fp_ids_user)

            fp_ids_event = (
                FingerprintEvent.objects.filter(
                    event_data__contains={field_name: phone.value}
                )
                .values_list("fingerprint_id", flat=True)
                .distinct()
            )
            fp_ids.update(fp_ids_event)

        fingerprints = FingerprintIdentity.objects.filter(id__in=fp_ids)

        associated = 0
        with transaction.atomic():
            for fp in fingerprints:
                FingerprintContact.objects.get_or_create(
                    fingerprint=fp,
                    content_type=ContentType.objects.get_for_model(ContactPhone),
                    object_id=phone.id,
                    defaults={
                        "verification_status": "unverified",
                        "first_seen": timezone.now(),
                        "last_seen": timezone.now(),
                    },
                )
                associated += 1

                # Link phone to fingerprint's identity if not yet linked
                if not phone.identity and fp.identity:
                    phone.identity = fp.identity
                    phone.save(update_fields=["identity", "updated_at"])

        logger.info("Associated phone %s with %d fingerprints", phone.value, associated)
        return {
            "status": "success",
            "phone_id": phone.public_id,
            "fingerprints_associated": associated,
        }

    except Exception as e:
        logger.exception(
            "Error associating phone %d with fingerprints: %s", phone_id, str(e)
        )
        raise


@shared_task(
    name="contact_phone.verify",
    queue="contact_verification",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 300},
    acks_late=True,
)
def verify_phone(phone_id: int) -> dict:
    """
    Send phone verification SMS and trigger confidence recalculation.

    Args:
        phone_id: Primary key of the ContactPhone.
    """
    try:
        from apps.contacts.phone.models import ContactPhone
        from apps.contacts.email.services.verification_service import (
            VerificationService,
        )

        phone = ContactPhone.objects.filter(id=phone_id).first()
        if not phone:
            return {"status": "error", "message": f"Phone {phone_id} not found"}

        result = VerificationService.send_phone_verification(phone)

        # Recalculate identity confidence
        if phone.identity_id:
            from apps.contacts.identity.tasks import calculate_confidence_score

            calculate_confidence_score.delay(phone.identity_id)

        logger.info("Sent verification for phone %s", phone.value)
        return {
            "status": "success",
            "phone_id": phone.public_id,
            "verification_sent": True,
        }

    except Exception as e:
        logger.exception("Error verifying phone %d: %s", phone_id, str(e))
        raise


@shared_task(
    name="contact_phone.confirm_verification",
    queue="contact_verification",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def confirm_phone_verification(phone_id: int, code: str) -> dict:
    """
    Confirm phone verification with a code.

    Args:
        phone_id: Primary key of the ContactPhone.
        code: Verification code.
    """
    try:
        from apps.contacts.phone.models import ContactPhone
        from apps.contacts.email.services.verification_service import (
            VerificationService,
        )

        phone = ContactPhone.objects.filter(id=phone_id).first()
        if not phone:
            return {"status": "error", "message": f"Phone {phone_id} not found"}

        verified = VerificationService.verify_phone_with_code(phone, code)

        # Recalculate identity confidence after verification
        if phone.identity_id and verified:
            from apps.contacts.identity.tasks import calculate_confidence_score

            calculate_confidence_score.delay(phone.identity_id)

        return {
            "status": "success" if verified else "error",
            "phone_id": phone.public_id,
            "verified": verified,
        }

    except Exception as e:
        logger.exception("Error confirming phone %d: %s", phone_id, str(e))
        raise
