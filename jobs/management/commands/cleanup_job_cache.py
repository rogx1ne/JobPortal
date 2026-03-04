from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import ApiFetchLog, JobCache


class Command(BaseCommand):
    help = "Deletes old cached jobs and API fetch logs."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--job-days", type=int, default=30, help="Delete JobCache older than N days (default: 30)")
        parser.add_argument("--api-days", type=int, default=7, help="Delete ApiFetchLog older than N days (default: 7)")

    def handle(self, *args, **options) -> None:
        job_days = max(1, int(options["job_days"]))
        api_days = max(1, int(options["api_days"]))

        now = timezone.now()
        job_cutoff = now - timedelta(days=job_days)
        api_cutoff = now - timedelta(days=api_days)

        deleted_jobs, _ = JobCache.objects.filter(fetched_at__lt=job_cutoff).delete()
        deleted_api, _ = ApiFetchLog.objects.filter(fetched_at__lt=api_cutoff).delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted JobCache rows: {deleted_jobs}"))
        self.stdout.write(self.style.SUCCESS(f"Deleted ApiFetchLog rows: {deleted_api}"))

