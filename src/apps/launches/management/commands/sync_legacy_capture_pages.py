"""Sync legacy JSON landing campaigns into CapturePage records.

Usage:
    uv run python manage.py sync_legacy_capture_pages
    uv run python manage.py sync_legacy_capture_pages --dry-run
    uv run python manage.py sync_legacy_capture_pages --slug wh-rc-v3
    uv run python manage.py sync_legacy_capture_pages --include-non-capture
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from apps.landing.campaigns import get_campaign
from apps.launches.services import CapturePageService


class Command(BaseCommand):
    help = "Sync legacy JSON campaign files into CapturePage records."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be synced without writing to the database.",
        )
        parser.add_argument(
            "--slug",
            type=str,
            help="Sync a single campaign slug only.",
        )
        parser.add_argument(
            "--include-non-capture",
            action="store_true",
            help="Include JSON configs that do not look like capture pages.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options["dry_run"]
        target_slug = options.get("slug")
        include_non_capture = options["include_non_capture"]

        campaigns_dir = (
            Path(__file__).resolve().parents[4] / "apps" / "landing" / "campaigns"
        )
        json_files = sorted(campaigns_dir.glob("*.json"))

        if target_slug:
            json_files = [path for path in json_files if path.stem == target_slug]

        if not json_files:
            self.stdout.write("No legacy JSON campaign files found.")
            return

        synced = 0
        skipped = 0

        for json_file in json_files:
            slug = json_file.stem
            config = get_campaign(slug)
            if config is None:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"Skipped {slug}: could not load JSON")
                )
                continue

            if not include_non_capture and not self._is_capture_like(config):
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"Skipped {slug}: non-capture config")
                )
                continue

            if dry_run:
                existing = CapturePageService.get_page(slug)
                action = "update" if existing is not None else "create"
                self.stdout.write(f"[DRY RUN] Would {action} CapturePage for {slug}")
                synced += 1
                continue

            page = CapturePageService.materialize_legacy_page(slug, config)
            synced += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced CapturePage: {page.slug} ({page.public_id})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete. synced={synced} skipped={skipped} dry_run={dry_run}"
            )
        )

    @staticmethod
    def _is_capture_like(config: dict[str, Any]) -> bool:
        """Heuristic to keep the command focused on capture-page runtime configs."""
        return "form" in config and "headline" in config
