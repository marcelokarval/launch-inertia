"""
Signal receivers for identity events.

Triggers async tasks when identities are created, updated, or merged.
Uses lazy imports to avoid circular import issues.

Ported from legacy identity/signals.py.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.contacts.identity.models import Identity
from apps.contacts.identity.signals_def import identity_post_merge

logger = logging.getLogger(__name__)


def _get_identity_tasks():
    """Lazy import to avoid circular dependency."""
    from apps.contacts.identity.tasks import (
        calculate_confidence_score,
        update_identity_history,
        analyze_identity_graph,
    )

    return calculate_confidence_score, update_identity_history, analyze_identity_graph


def _get_lifecycle_task():
    """Lazy import for lifecycle recalculation task."""
    from apps.contacts.identity.tasks import recalculate_lifecycle

    return recalculate_lifecycle


@receiver(post_save, sender=Identity)
def identity_post_save(sender, instance, created, **kwargs):
    """
    When an identity is created or updated, enqueue async tasks.

    On creation:
    - Calculate confidence score
    - Record creation in history
    - Analyze relationship graph
    """
    if created:
        logger.info("New identity created: %s", instance.public_id)

        calc_confidence, update_history, analyze_graph = _get_identity_tasks()
        recalc_lifecycle = _get_lifecycle_task()

        calc_confidence.delay(instance.id)
        update_history.delay(
            instance.id,
            "UPDATE",
            {"action": "created", "created_at": instance.created_at.isoformat()},
        )
        analyze_graph.delay(instance.id)
        recalc_lifecycle.delay(instance.id)


@receiver(identity_post_merge)
def identity_post_merge_handler(sender, source, target, stats, **kwargs):
    """
    After an identity merge, recalculate confidence and analyze graph
    for the surviving (target) identity.
    """
    logger.info(
        "Identity merge completed: %s -> %s",
        source.public_id if hasattr(source, "public_id") else str(source),
        target.public_id,
    )

    calc_confidence, _, analyze_graph = _get_identity_tasks()
    recalc_lifecycle = _get_lifecycle_task()

    calc_confidence.delay(target.id)
    analyze_graph.delay(target.id)
    recalc_lifecycle.delay(target.id)
