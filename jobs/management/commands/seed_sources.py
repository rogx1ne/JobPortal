from __future__ import annotations

from django.core.management.base import BaseCommand

from jobs.models import Source, SourceType


DEFAULT_SOURCES = [
    {
        "name": "Remotive API",
        "type": SourceType.API,
        "base_url": "https://remotive.com",
        "endpoint": "/api/remote-jobs",
        "frequency": 30,
    },
    {
        "name": "Arbeitnow API",
        "type": SourceType.API,
        "base_url": "https://www.arbeitnow.com",
        "endpoint": "/api/job-board-api",
        "frequency": 30,
    },
    {
        "name": "Example Company Careers",
        "type": SourceType.COMPANY,
        "base_url": "https://example.com",
        "endpoint": "/careers",
        "frequency": 180,
        "parser_config": {
            "company_name": "Example Inc",
            "card_selector": "a[href*='job'], a[href*='careers']",
        },
    },
]


class Command(BaseCommand):
    help = "Seed default ingestion sources for API and company pages."

    def handle(self, *args, **options):
        created_count = 0
        for source_data in DEFAULT_SOURCES:
            _, created = Source.objects.update_or_create(
                name=source_data["name"],
                defaults=source_data,
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded sources. New rows: {created_count}"))
