"""Requeue failed/pending lead integration outbox entries.

Usage:
    uv run python manage.py requeue_failed_lead_integrations
    uv run python manage.py requeue_failed_lead_integrations --integration-type n8n
    uv run python manage.py requeue_failed_lead_integrations --outbox-id lio_xxx
    uv run python manage.py requeue_failed_lead_integrations --status failed pending
    uv run python manage.py requeue_failed_lead_integrations --dry-run
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.landing.models import LeadIntegrationOutbox
from apps.landing.tasks import process_lead_integration_outbox_task


class Command(BaseCommand):
    help = "Requeue lead integration outbox entries for processing."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--outbox-id",
            type=str,
            help="Requeue one specific LeadIntegrationOutbox by public_id.",
        )
        parser.add_argument(
            "--integration-type",
            type=str,
            choices=[
                LeadIntegrationOutbox.IntegrationType.N8N,
                LeadIntegrationOutbox.IntegrationType.META_CAPI,
            ],
            help="Filter by integration type.",
        )
        parser.add_argument(
            "--status",
            nargs="+",
            choices=[
                LeadIntegrationOutbox.Status.PENDING,
                LeadIntegrationOutbox.Status.PROCESSING,
                LeadIntegrationOutbox.Status.SENT,
                LeadIntegrationOutbox.Status.FAILED,
                LeadIntegrationOutbox.Status.SKIPPED,
            ],
            default=[LeadIntegrationOutbox.Status.FAILED],
            help="Statuses eligible for requeue. Default: failed",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of outbox entries to requeue. Default: 100",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be requeued without mutating records.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        queryset = LeadIntegrationOutbox.objects.all().order_by("created_at")

        outbox_id = options.get("outbox_id")
        if outbox_id:
            queryset = queryset.filter(public_id=outbox_id)

        integration_type = options.get("integration_type")
        if integration_type:
            queryset = queryset.filter(integration_type=integration_type)

        statuses = options.get("status") or [LeadIntegrationOutbox.Status.FAILED]
        queryset = queryset.filter(status__in=statuses)

        limit = max(1, options.get("limit") or 100)
        entries = list(queryset[:limit])

        if not entries:
            self.stdout.write("No outbox entries matched the provided filters.")
            return

        dry_run = options["dry_run"]
        if dry_run:
            for entry in entries:
                self.stdout.write(
                    f"[DRY RUN] Would requeue {entry.public_id} ({entry.integration_type}, {entry.status})"
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run complete. matched={len(entries)} limit={limit}"
                )
            )
            return

        requeued = 0
        for entry in entries:
            entry.status = LeadIntegrationOutbox.Status.PENDING
            entry.last_error = ""
            entry.next_retry_at = None
            entry.processed_at = None
            entry.save(
                update_fields=[
                    "status",
                    "last_error",
                    "next_retry_at",
                    "processed_at",
                    "updated_at",
                ]
            )
            process_lead_integration_outbox_task.delay(entry.public_id)
            requeued += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Requeued {entry.public_id} ({entry.integration_type})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Requeue complete. requeued={requeued} limit={limit}")
        )
