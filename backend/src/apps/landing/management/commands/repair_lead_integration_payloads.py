"""Repair incomplete LeadIntegrationOutbox payloads using persisted submissions.

Usage:
    uv run python manage.py repair_lead_integration_payloads
    uv run python manage.py repair_lead_integration_payloads --outbox-id lio_xxx
    uv run python manage.py repair_lead_integration_payloads --integration-type n8n
    uv run python manage.py repair_lead_integration_payloads --dry-run
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.landing.models import LeadIntegrationOutbox
from core.shared.hashing import hash_email, hash_phone


class Command(BaseCommand):
    help = "Repair incomplete lead integration outbox payloads from submissions."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--outbox-id", type=str, help="Repair one specific outbox entry."
        )
        parser.add_argument(
            "--integration-type",
            type=str,
            choices=[
                LeadIntegrationOutbox.IntegrationType.N8N,
                LeadIntegrationOutbox.IntegrationType.META_CAPI,
            ],
            help="Restrict repair to one integration type.",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview without saving."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        queryset = LeadIntegrationOutbox.objects.select_related(
            "capture_submission", "capture_submission__identity"
        ).all()

        if options.get("outbox_id"):
            queryset = queryset.filter(public_id=options["outbox_id"])
        if options.get("integration_type"):
            queryset = queryset.filter(integration_type=options["integration_type"])

        repaired = 0
        inspected = 0
        dry_run = options["dry_run"]

        for outbox in queryset.order_by("created_at"):
            inspected += 1
            updated = self._repair_outbox(outbox, dry_run=dry_run)
            if updated:
                repaired += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Repair complete. inspected={inspected} repaired={repaired} dry_run={dry_run}"
            )
        )

    def _repair_outbox(self, outbox: LeadIntegrationOutbox, *, dry_run: bool) -> bool:
        submission = outbox.capture_submission
        if submission is None:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {outbox.public_id}: no capture_submission linked"
                )
            )
            return False

        payload = dict(outbox.payload or {})
        changed = False

        if not outbox.identity_public_id and submission.identity_id:
            outbox.identity_public_id = submission.identity.public_id
            changed = True

        if outbox.integration_type == LeadIntegrationOutbox.IntegrationType.N8N:
            if payload.get("submission_id") != submission.public_id:
                payload["submission_id"] = submission.public_id
                changed = True

        elif outbox.integration_type == LeadIntegrationOutbox.IntegrationType.META_CAPI:
            if not payload.get("external_id") and submission.identity_id:
                payload["external_id"] = submission.identity.public_id
                changed = True

            if not payload.get("email_hash") and submission.email_raw:
                try:
                    payload["email_hash"] = hash_email(submission.email_raw)
                    changed = True
                except ValueError:
                    pass

            if not payload.get("phone_hash") and submission.phone_raw:
                try:
                    payload["phone_hash"] = hash_phone(submission.phone_raw)
                    changed = True
                except ValueError:
                    pass

            if not payload.get("event_id"):
                payload["event_id"] = str(submission.capture_token)
                changed = True

        if not changed:
            self.stdout.write(f"Unchanged {outbox.public_id}")
            return False

        if dry_run:
            self.stdout.write(f"[DRY RUN] Would repair {outbox.public_id}")
            return True

        outbox.payload = payload
        outbox.save(update_fields=["payload", "identity_public_id", "updated_at"])
        self.stdout.write(self.style.SUCCESS(f"Repaired {outbox.public_id}"))
        return True
