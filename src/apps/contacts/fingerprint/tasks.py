"""
Celery tasks for fingerprint processing.

Async processing for:
- FingerprintJS event processing
- Fingerprint data updates
- Pattern analysis
- Suspicious activity detection
- Identity merge via fingerprint

Ported from legacy fingerprint/tasks.py.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="contact_fingerprint.process_event",
    queue="fingerprint_events",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def process_fingerprint_event(event_data: dict) -> dict:
    """
    Process a fingerprint event asynchronously.

    This is the main entry point for incoming FingerprintJS Pro webhooks.
    Delegates to EventService.process_event() which orchestrates the full
    resolution pipeline.

    Args:
        event_data: Dict with fingerprint, contact, and session data.
    """
    try:
        from apps.contacts.fingerprint.services.event_service import EventService

        result = EventService.process_event(event_data)

        logger.info(
            "Processed fingerprint event: %s", event_data.get("event_type", "unknown")
        )
        return result

    except Exception as e:
        logger.exception("Error processing fingerprint event: %s", str(e))
        raise


@shared_task(
    name="contact_fingerprint.update_data",
    queue="fingerprint_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def update_fingerprint_data(fingerprint_id: int, new_data: dict) -> dict:
    """
    Update fingerprint data with new information from FingerprintJS Pro.

    Args:
        fingerprint_id: Primary key of FingerprintIdentity.
        new_data: New device/browser/geo data from FingerprintJS Pro.
    """
    try:
        from apps.contacts.fingerprint.models import FingerprintIdentity
        from apps.contacts.fingerprint.services.fingerprint_service import (
            FingerprintService,
        )

        fp = FingerprintIdentity.objects.filter(id=fingerprint_id).first()
        if not fp:
            return {
                "status": "error",
                "message": f"Fingerprint {fingerprint_id} not found",
            }

        service = FingerprintService()
        service.update_fingerprint_data(fp, new_data)

        logger.info("Updated fingerprint data for %s", fp.hash[:12])
        return {
            "status": "success",
            "fingerprint_id": fp.public_id,
        }

    except Exception as e:
        logger.exception("Error updating fingerprint %d: %s", fingerprint_id, str(e))
        raise


@shared_task(
    name="contact_fingerprint.analyze_patterns",
    queue="fingerprint_analysis",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def analyze_fingerprint_patterns(identity_id: int) -> dict:
    """
    Analyze fingerprint usage patterns for an identity.

    Looks for anomalies like too many devices, rapid device switching,
    incognito usage, etc.

    Args:
        identity_id: Primary key of the Identity whose fingerprints to analyze.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.fingerprint.services.fingerprint_service import (
            FingerprintService,
        )

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        service = FingerprintService()
        # analyze_fingerprint_patterns expects an Identity (not FingerprintIdentity)
        analysis = service.analyze_fingerprint_patterns(identity)

        logger.info("Analyzed fingerprint patterns for identity %s", identity.public_id)
        return {
            "status": "success",
            "identity_id": identity.public_id,
            "analysis": analysis,
        }

    except Exception as e:
        logger.exception(
            "Error analyzing patterns for identity %d: %s", identity_id, str(e)
        )
        raise


@shared_task(
    name="contact_fingerprint.detect_suspicious",
    queue="fingerprint_security",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def detect_suspicious_activity(fingerprint_id: int) -> dict:
    """
    Detect suspicious activity for a fingerprint.

    Checks for incognito mode, VPN, bot signals, etc.

    Args:
        fingerprint_id: Primary key of FingerprintIdentity.
    """
    try:
        from apps.contacts.fingerprint.models import FingerprintIdentity
        from apps.contacts.fingerprint.services.fingerprint_service import (
            FingerprintService,
        )

        fp = FingerprintIdentity.objects.filter(id=fingerprint_id).first()
        if not fp:
            return {
                "status": "error",
                "message": f"Fingerprint {fingerprint_id} not found",
            }

        service = FingerprintService()
        detection = service.detect_suspicious_activity(fp)

        logger.info("Suspicious activity check for fingerprint %s", fp.hash[:12])
        return {
            "status": "success",
            "fingerprint_id": fp.public_id,
            "detection": detection,
        }

    except Exception as e:
        logger.exception(
            "Error detecting suspicious activity for %d: %s", fingerprint_id, str(e)
        )
        raise


@shared_task(
    name="contact_fingerprint.merge_identities",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def merge_identities_from_fingerprint(source_id: int, target_id: int) -> dict:
    """
    Merge two identities discovered via shared fingerprint.

    Delegates to identity.tasks.merge_identities.

    Args:
        source_id: Primary key of the source Identity.
        target_id: Primary key of the target Identity.
    """
    try:
        from apps.contacts.identity.tasks import merge_identities

        result = merge_identities(source_id, target_id)
        return result

    except Exception as e:
        logger.exception(
            "Error merging identities %d -> %d from fingerprint: %s",
            source_id,
            target_id,
            str(e),
        )
        raise
