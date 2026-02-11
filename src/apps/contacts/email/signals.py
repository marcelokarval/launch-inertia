"""
Signal receivers for ContactEmail events.

Triggers async tasks when emails are created or updated.
No WebSocket broadcasting (unlike legacy) — Inertia handles
real-time UI updates via page refreshes.

Ported from legacy contact/signals.py (email-related receivers).
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.contacts.email.models import ContactEmail

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ContactEmail)
def email_post_save(sender, instance, created, **kwargs):
    """
    When a ContactEmail is created, enqueue processing and verification tasks.
    """
    if created:
        logger.info("New contact email created: %s", instance.value)

        from apps.contacts.email.tasks import process_new_email, verify_email

        process_new_email.delay(instance.value)
        verify_email.delay(instance.id)
