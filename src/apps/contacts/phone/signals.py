"""
Signal receivers for ContactPhone events.

Triggers async tasks when phones are created or updated.

Ported from legacy contact/signals.py (phone-related receivers).
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.contacts.phone.models import ContactPhone

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ContactPhone)
def phone_post_save(sender, instance, created, **kwargs):
    """
    When a ContactPhone is created, enqueue processing and verification tasks.
    """
    if created:
        logger.info("New contact phone created: %s", instance.value)

        from apps.contacts.phone.tasks import process_new_phone, verify_phone

        process_new_phone.delay(instance.value)
        verify_phone.delay(instance.id)

        # Trigger lifecycle recalculation for the linked identity
        if instance.identity_id:
            from apps.contacts.identity.tasks import recalculate_lifecycle

            recalculate_lifecycle.delay(instance.identity_id)
