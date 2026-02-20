"""
Celery tasks for identity resolution.

Async processing for:
- Confidence score calculation
- Merge candidate discovery + auto-merge
- Identity history updates
- Graph analysis
- Cleanup of merged identities

Ported from legacy identity/tasks.py.
"""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name="identity.calculate_confidence_score",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def calculate_confidence_score(identity_id: int) -> dict:
    """
    Calculate the confidence score for an identity.

    Args:
        identity_id: Primary key of the Identity object.
    """
    try:
        from apps.contacts.identity.models import Identity

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            logger.error("Identity %d not found", identity_id)
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        from apps.contacts.identity.services.confidence_engine import ConfidenceEngine

        score = ConfidenceEngine.calculate(identity)

        logger.info(
            "Calculated confidence score %.2f for identity %s",
            score,
            identity.public_id,
        )
        return {
            "status": "success",
            "identity_id": identity.public_id,
            "confidence_score": score,
        }

    except Exception as e:
        logger.exception(
            "Error calculating confidence for identity %d: %s", identity_id, str(e)
        )
        raise


@shared_task(
    name="identity.find_merge_candidates",
    queue="identity_analysis",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def find_merge_candidates() -> dict:
    """
    Scan all active identities for merge candidates.

    Auto-merges candidates with confidence >= 0.9.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.merge_service import MergeService

        active_identities = Identity.objects.filter(status=Identity.ACTIVE)
        all_candidates = []

        for identity in active_identities:
            candidates = MergeService.find_merge_candidates(identity)

            for candidate in candidates:
                all_candidates.append(
                    {
                        "source_id": identity.public_id,
                        "target_id": candidate["identity"].public_id,
                        "match_type": candidate["match_type"],
                        "confidence": candidate["confidence"],
                    }
                )

                # Auto-merge high confidence
                if candidate["confidence"] >= 0.9:
                    merge_identities.delay(identity.id, candidate["identity_id"])

        logger.info("Found %d merge candidates", len(all_candidates))
        return {
            "status": "success",
            "candidates_found": len(all_candidates),
        }

    except Exception as e:
        logger.exception("Error finding merge candidates: %s", str(e))
        raise


@shared_task(
    name="identity.merge_identities",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def merge_identities(source_id: int, target_id: int) -> dict:
    """
    Merge source identity into target identity.

    Args:
        source_id: Primary key of the source Identity.
        target_id: Primary key of the target Identity.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.merge_service import MergeService

        source = Identity.objects.filter(id=source_id).first()
        target = Identity.objects.filter(id=target_id).first()

        if not source or not target:
            return {
                "status": "error",
                "message": f"Identity not found: source={source_id}, target={target_id}",
            }

        stats = MergeService.execute_merge(source, target)

        logger.info("Merged identity %s into %s", source.public_id, target.public_id)
        return {
            "status": "success",
            "source": source.public_id,
            "target": target.public_id,
            "stats": stats,
        }

    except Exception as e:
        logger.exception("Error merging %d -> %d: %s", source_id, target_id, str(e))
        raise


@shared_task(
    name="identity.auto_merge",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def auto_merge(identity_id: int) -> dict:
    """
    Auto-merge high-confidence candidates into the given identity.

    Args:
        identity_id: Primary key of the Identity to check for duplicates.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.merge_service import MergeService

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        results = MergeService.auto_merge_identities(identity)

        logger.info("Auto-merge for %s: %d merges", identity.public_id, len(results))
        return {
            "status": "success",
            "identity_id": identity.public_id,
            "merged_count": len(results),
        }

    except Exception as e:
        logger.exception("Error auto-merging identity %d: %s", identity_id, str(e))
        raise


@shared_task(
    name="identity.update_history",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def update_identity_history(
    identity_id: int,
    operation_type: str,
    details: dict | None = None,
) -> dict:
    """
    Create a history record for an identity operation.

    Args:
        identity_id: Primary key of the Identity.
        operation_type: One of IdentityHistory operation types.
        details: Optional JSON-serializable dict with context.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.identity_service import IdentityService

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        history = IdentityService.update_identity_history(
            identity, operation_type, details or {}
        )

        return {
            "status": "success",
            "identity_id": identity.public_id,
            "history_id": history.public_id,
        }

    except Exception as e:
        logger.exception(
            "Error updating history for identity %d: %s", identity_id, str(e)
        )
        raise


@shared_task(
    name="identity.analyze_graph",
    queue="identity_analysis",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 300},
    acks_late=True,
)
def analyze_identity_graph(identity_id: int) -> dict:
    """
    Analyze the relationship graph of an identity.

    Args:
        identity_id: Primary key of the Identity.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.analysis_service import AnalysisService

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        graph = AnalysisService.analyze_identity_graph(identity)

        logger.info("Analyzed graph for identity %s", identity.public_id)
        return {
            "status": "success",
            "identity_id": identity.public_id,
            "graph": graph,
        }

    except Exception as e:
        logger.exception(
            "Error analyzing graph for identity %d: %s", identity_id, str(e)
        )
        raise


@shared_task(
    name="identity.cleanup_merged",
    queue="identity_maintenance",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def cleanup_merged_identities(days: int = 30) -> dict:
    """
    Delete merged identities older than `days` that have no remaining references.

    Runs as a periodic task (celery beat).
    """
    try:
        from apps.contacts.identity.models import Identity, IdentityHistory
        from apps.contacts.email.models import ContactEmail
        from apps.contacts.phone.models import ContactPhone
        from apps.contacts.fingerprint.models import FingerprintIdentity

        cutoff = timezone.now() - timedelta(days=days)

        old_merged = Identity.objects.filter(
            status=Identity.MERGED,
            updated_at__lt=cutoff,
        )

        total = old_merged.count()
        deleted = 0

        batch_size = 100
        for i in range(0, total, batch_size):
            batch = old_merged[i : i + batch_size]

            with transaction.atomic():
                for identity in batch:
                    has_refs = (
                        ContactEmail.objects.filter(identity=identity).exists()
                        or ContactPhone.objects.filter(identity=identity).exists()
                        or FingerprintIdentity.objects.filter(
                            identity=identity
                        ).exists()
                    )

                    if not has_refs:
                        IdentityHistory.objects.filter(identity=identity).delete()
                        identity.delete()
                        deleted += 1

        logger.info(
            "Cleaned up %d/%d merged identities (cutoff: %d days)", deleted, total, days
        )
        return {
            "status": "success",
            "identities_processed": total,
            "identities_deleted": deleted,
        }

    except Exception as e:
        logger.exception("Error cleaning up merged identities: %s", str(e))
        raise


@shared_task(
    name="identity.recalculate_lifecycle",
    queue="identity_processing",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    acks_late=True,
)
def recalculate_lifecycle(identity_id: int) -> dict:
    """
    Recalculate the lifecycle_global JSONB cache for an identity.

    Triggered by signals when channels/tags/fingerprints change,
    or after merge operations.

    Args:
        identity_id: Primary key of the Identity object.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.lifecycle_service import LifecycleService

        identity = Identity.objects.filter(id=identity_id).first()
        if not identity:
            logger.error(
                "Identity %d not found for lifecycle recalculation", identity_id
            )
            return {"status": "error", "message": f"Identity {identity_id} not found"}

        lifecycle = LifecycleService.recalculate(identity)

        logger.info(
            "Recalculated lifecycle for identity %s (version=%s)",
            identity.public_id,
            lifecycle.get("_version"),
        )
        return {
            "status": "success",
            "identity_id": identity.public_id,
            "version": lifecycle.get("_version"),
        }

    except Exception as e:
        logger.exception(
            "Error recalculating lifecycle for identity %d: %s", identity_id, str(e)
        )
        raise


@shared_task(
    name="identity.bulk_recalculate_lifecycle",
    queue="identity_maintenance",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 300},
    acks_late=True,
)
def bulk_recalculate_lifecycle(batch_size: int = 100) -> dict:
    """
    Recalculate lifecycle_global for all active identities.

    Useful for schema migrations or after bulk data imports.
    Processes in batches to avoid memory issues.
    """
    try:
        from apps.contacts.identity.models import Identity

        active_identities = Identity.objects.filter(
            status=Identity.ACTIVE,
            is_deleted=False,
        )
        total = active_identities.count()
        processed = 0
        errors = 0

        for identity in active_identities.iterator(chunk_size=batch_size):
            try:
                recalculate_lifecycle.delay(identity.id)
                processed += 1
            except Exception as e:
                logger.warning(
                    "Failed to queue lifecycle recalculation for %s: %s",
                    identity.public_id,
                    str(e),
                )
                errors += 1

        logger.info(
            "Queued lifecycle recalculation for %d/%d identities (%d errors)",
            processed,
            total,
            errors,
        )
        return {
            "status": "success",
            "total": total,
            "queued": processed,
            "errors": errors,
        }

    except Exception as e:
        logger.exception("Error in bulk lifecycle recalculation: %s", str(e))
        raise


@shared_task(
    name="identity.batch_merge_recent",
    queue="identity_analysis",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 300},
    acks_late=True,
    time_limit=600,  # 10 min hard limit
    soft_time_limit=540,  # 9 min soft limit
)
def batch_merge_recent(lookback_days: int = 7) -> dict:
    """Batch merge task for recently active identities.

    Runs periodically (every 6h via celery beat). Scans identities
    that had activity in the last `lookback_days` and:
    1. Auto-merges candidates with confidence >= 0.9
    2. Stores household hints (0.3) in identity metadata

    Only processes ACTIVE identities with recent CaptureEvents.
    Limits to 500 identities per run to avoid timeouts.

    Args:
        lookback_days: How far back to look for active identities.

    Returns:
        Stats dict with counts of processed, merged, and household flags.
    """
    try:
        from apps.contacts.identity.models import Identity
        from apps.contacts.identity.services.merge_service import (
            MergeService,
            MergeValidationError,
        )
        from core.tracking.models import CaptureEvent

        now = timezone.now()
        cutoff = now - timedelta(days=lookback_days)
        max_identities = 500

        # Find identities with recent events
        recent_identity_pks = (
            CaptureEvent.objects.filter(
                identity__isnull=False,
                identity__status=Identity.ACTIVE,
                created_at__gte=cutoff,
            )
            .values_list("identity_id", flat=True)
            .distinct()[:max_identities]
        )

        recent_identities = Identity.objects.filter(
            pk__in=recent_identity_pks,
            status=Identity.ACTIVE,
            is_deleted=False,
        )

        stats = {
            "identities_scanned": 0,
            "merges_executed": 0,
            "merge_errors": 0,
            "household_flags": 0,
        }

        for identity in recent_identities.iterator(chunk_size=50):
            stats["identities_scanned"] += 1

            try:
                candidates = MergeService.find_merge_candidates(identity)

                for candidate in candidates:
                    confidence = candidate["confidence"]

                    if confidence >= 0.9:
                        # Auto-merge: dispatch individual merge task
                        candidate_identity = candidate["identity"]
                        try:
                            # Oldest survives
                            if candidate_identity.created_at < identity.created_at:
                                MergeService.execute_merge(identity, candidate_identity)
                            else:
                                MergeService.execute_merge(candidate_identity, identity)
                            stats["merges_executed"] += 1
                        except MergeValidationError as e:
                            logger.debug("Batch merge skipped: %s", str(e))
                            stats["merge_errors"] += 1
                        except Exception:
                            logger.debug(
                                "Batch merge error for %s",
                                identity.public_id,
                                exc_info=True,
                            )
                            stats["merge_errors"] += 1

                        # If our identity was merged away, stop processing it
                        identity.refresh_from_db(fields=["status"])
                        if identity.status != Identity.ACTIVE:
                            break

                    elif candidate["match_type"] == "ip_household":
                        # Household hint: store in metadata (no merge)
                        candidate_identity = candidate["identity"]
                        _store_household_hint(identity, candidate_identity)
                        stats["household_flags"] += 1

            except Exception:
                logger.debug(
                    "Error scanning identity %s for merge candidates",
                    identity.public_id,
                    exc_info=True,
                )

        logger.info(
            "Batch merge complete: scanned=%d, merged=%d, errors=%d, household=%d",
            stats["identities_scanned"],
            stats["merges_executed"],
            stats["merge_errors"],
            stats["household_flags"],
        )
        return {"status": "success", **stats}

    except Exception as e:
        logger.exception("Error in batch_merge_recent: %s", str(e))
        raise


def _store_household_hint(identity: Any, candidate: Any) -> None:
    """Store a household hint in both identities' metadata.

    Household hints are low-confidence (0.3) signals that two identities
    may belong to people in the same household (same IP, different OS).
    They are NEVER auto-merged — only stored for manual review or
    future analytics.
    """
    try:
        for target, other in [(identity, candidate), (candidate, identity)]:
            metadata = target.metadata or {}
            household = metadata.get("household_hints", [])

            # Avoid duplicates
            existing_pids = {h.get("identity_id") for h in household}
            if other.public_id not in existing_pids:
                household.append(
                    {
                        "identity_id": other.public_id,
                        "detected_at": timezone.now().isoformat(),
                        "match_type": "ip_household",
                    }
                )
                # Keep only last 10 hints
                metadata["household_hints"] = household[-10:]
                target.metadata = metadata
                target.save(update_fields=["metadata", "updated_at"])
    except Exception:
        logger.debug(
            "Failed to store household hint for %s / %s",
            identity.public_id,
            candidate.public_id,
            exc_info=True,
        )
