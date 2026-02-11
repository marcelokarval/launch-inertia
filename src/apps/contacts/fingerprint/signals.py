"""
Signal receivers for fingerprint events.

Triggers async tasks when FingerprintEvents or FingerprintIdentity
records are created or updated.

Ported from legacy fingerprint/signals.py.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.contacts.fingerprint.models import FingerprintEvent, FingerprintIdentity

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FingerprintEvent)
def fingerprint_event_post_save(sender, instance, created, **kwargs):
    """
    When a FingerprintEvent is created, process it and trigger analysis.
    """
    if created:
        logger.info("New fingerprint event: %s", instance.event_type)

        from apps.contacts.fingerprint.tasks import (
            analyze_fingerprint_patterns,
            detect_suspicious_activity,
        )

        # If the fingerprint has an identity, analyze patterns
        if instance.fingerprint.identity_id:
            analyze_fingerprint_patterns.delay(instance.fingerprint.identity_id)

        # Detect suspicious activity on the fingerprint
        detect_suspicious_activity.delay(instance.fingerprint_id)


@receiver(post_save, sender=FingerprintIdentity)
def fingerprint_identity_post_save(sender, instance, created, **kwargs):
    """
    When a FingerprintIdentity is created or its identity changes,
    trigger pattern analysis.
    """
    if created:
        logger.info("New fingerprint identity: %s", instance.hash[:12])

        if instance.identity_id:
            from apps.contacts.fingerprint.tasks import analyze_fingerprint_patterns

            analyze_fingerprint_patterns.delay(instance.identity_id)
