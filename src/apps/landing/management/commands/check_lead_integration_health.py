"""Check health of lead integration outbox against operational thresholds."""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.landing.services.outbox import LeadIntegrationOutboxMonitoringService


class Command(BaseCommand):
    help = "Check LeadIntegrationOutbox health against failed/pending thresholds."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--json", action="store_true", help="Output JSON only.")
        parser.add_argument(
            "--failed-threshold", type=int, help="Override failed threshold."
        )
        parser.add_argument(
            "--pending-threshold", type=int, help="Override stale pending threshold."
        )
        parser.add_argument(
            "--pending-max-age-minutes",
            type=int,
            help="Override pending max age in minutes.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        snapshot = LeadIntegrationOutboxMonitoringService.get_health_snapshot(
            failed_threshold=options.get("failed_threshold"),
            pending_threshold=options.get("pending_threshold"),
            pending_max_age_minutes=options.get("pending_max_age_minutes"),
        )

        if options["json"]:
            self.stdout.write(json.dumps(snapshot, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                "LeadIntegrationOutbox health: "
                f"healthy={snapshot['healthy']} "
                f"failed={snapshot['failed_count']} "
                f"pending={snapshot['pending_count']} "
                f"stale_pending={snapshot['stale_pending_count']} "
                f"processing={snapshot['processing_count']}"
            )
            if snapshot["reasons"]:
                for reason in snapshot["reasons"]:
                    self.stdout.write(f"- {reason}")

        if not snapshot["healthy"]:
            raise CommandError("Lead integration outbox health check failed")
