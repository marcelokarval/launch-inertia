"""
Management command to migrate existing JSON campaign files into the database.

Usage:
    uv run python manage.py migrate_campaigns
    uv run python manage.py migrate_campaigns --dry-run
"""

import json
import logging
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from apps.launches.models import CapturePage, Interest, Launch

logger = logging.getLogger(__name__)

# Maps campaign slug prefixes to interest slugs
INTEREST_MAP: dict[str, dict[str, str]] = {
    "rc": {"name": "Renda Com", "slug": "rc"},
    "td": {"name": "Trabalho Digital", "slug": "td"},
    "ds": {"name": "Do Zero ao Sucesso", "slug": "ds"},
    "cp": {"name": "Como Publicar", "slug": "cp"},
    "bf": {"name": "Black Friday", "slug": "bf"},
}


class Command(BaseCommand):
    help = "Migrate JSON campaign files from apps/landing/campaigns/ to database."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be created without writing to DB.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options["dry_run"]
        campaigns_dir = (
            Path(__file__).resolve().parents[4] / "apps" / "landing" / "campaigns"
        )

        if not campaigns_dir.exists():
            self.stderr.write(f"Campaigns dir not found: {campaigns_dir}")
            return

        json_files = list(campaigns_dir.glob("*.json"))
        if not json_files:
            self.stdout.write("No JSON campaign files found.")
            return

        self.stdout.write(f"Found {len(json_files)} campaign file(s).")

        # Ensure default launch exists
        if not dry_run:
            launch, created = Launch.objects.get_or_create(
                launch_code="WH0126",
                defaults={
                    "name": "Workshop Janeiro 2026",
                    "status": Launch.Status.ACTIVE,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created Launch: {launch}"))
        else:
            self.stdout.write("  [DRY RUN] Would create Launch: WH0126")

        for json_file in json_files:
            slug = json_file.stem  # e.g. "wh-rc-v3"
            self.stdout.write(f"\nProcessing: {slug}")

            with open(json_file) as f:
                config = json.load(f)

            # Detect interest from slug
            interest_key = self._detect_interest(slug)
            if interest_key and not dry_run:
                interest_data = INTEREST_MAP[interest_key]
                interest, _ = Interest.objects.get_or_create(
                    slug=interest_data["slug"],
                    defaults={"name": interest_data["name"]},
                )
            else:
                interest = None

            # Extract n8n fields from config
            n8n = config.get("n8n", {})
            n8n_webhook = n8n.get("webhook_url", "")
            n8n_list_id = n8n.get("list_id", "")

            if dry_run:
                self.stdout.write(f"  [DRY RUN] Would create CapturePage: {slug}")
                self.stdout.write(f"    interest: {interest_key or 'none'}")
                self.stdout.write(f"    n8n_webhook: {n8n_webhook[:60]}...")
                self.stdout.write(f"    config keys: {list(config.keys())}")
                continue

            # Create or update CapturePage
            page, created = CapturePage.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": config.get("meta", {}).get("title", slug),
                    "launch": launch,
                    "interest": interest,
                    "page_type": CapturePage.PageType.CAPTURE,
                    "config": config,
                    "n8n_webhook_url": n8n_webhook,
                    "n8n_list_id": n8n_list_id,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"  {action} CapturePage: {page}"))

        self.stdout.write(self.style.SUCCESS("\nMigration complete."))

    def _detect_interest(self, slug: str) -> str | None:
        """Detect interest key from slug pattern like wh-rc-v3, wh-td-v1, bf-v1."""
        parts = slug.split("-")
        for part in parts:
            if part in INTEREST_MAP:
                return part
        return None
