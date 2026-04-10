"""Audit whether legacy landing slugs are ready to run without JSON fallback.

Usage:
    uv run python manage.py check_capture_page_readiness
    uv run python manage.py check_capture_page_readiness --strict
    uv run python manage.py check_capture_page_readiness --include-non-capture
    uv run python manage.py check_capture_page_readiness --slug wh-rc-v3
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.landing.campaigns import get_campaign
from apps.launches.services import CapturePageService


class Command(BaseCommand):
    help = "Audit CapturePage readiness before disabling JSON fallback."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--slug",
            type=str,
            help="Audit a single campaign slug only.",
        )
        parser.add_argument(
            "--include-non-capture",
            action="store_true",
            help="Include JSON configs that do not look like capture pages.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with error if any required slug is missing in CapturePage.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        target_slug = options.get("slug")
        include_non_capture = options["include_non_capture"]
        strict = options["strict"]

        campaigns_dir = (
            Path(__file__).resolve().parents[4] / "apps" / "landing" / "campaigns"
        )
        json_files = sorted(campaigns_dir.glob("*.json"))

        if target_slug:
            json_files = [path for path in json_files if path.stem == target_slug]

        if not json_files:
            self.stdout.write("No legacy JSON campaign files found.")
            return

        checked = 0
        ready = 0
        missing: list[str] = []
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

            checked += 1
            page = CapturePageService.get_page(slug)
            if page is None:
                missing.append(slug)
                self.stdout.write(self.style.ERROR(f"MISSING  {slug}"))
            else:
                ready += 1
                self.stdout.write(
                    self.style.SUCCESS(f"READY    {slug} -> {page.public_id}")
                )

        summary = (
            f"Readiness complete. checked={checked} ready={ready} "
            f"missing={len(missing)} skipped={skipped}"
        )
        if missing:
            self.stdout.write(self.style.WARNING(summary))
            if strict:
                raise CommandError(
                    "CapturePage readiness check failed. Missing slugs: "
                    + ", ".join(missing)
                )
            return

        self.stdout.write(self.style.SUCCESS(summary))

    @staticmethod
    def _is_capture_like(config: dict[str, Any]) -> bool:
        return "form" in config and "headline" in config
