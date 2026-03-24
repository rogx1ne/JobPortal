from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from jobs.models import Source, SourceType
from services.ingestion_service import ingest_api_source, ingest_company_source, source_is_due


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_source_task(self, source_id: int) -> dict:
    source = Source.objects.filter(id=source_id, is_active=True).first()
    if source is None:
        return {"source_id": source_id, "ok": False, "error": "source_not_found"}

    if source.type == SourceType.API:
        result = ingest_api_source(source)
    else:
        result = ingest_company_source(source)
    return {
        "source_id": result.source_id,
        "source_name": result.source_name,
        "ok": result.ok,
        "created": result.created,
        "updated": result.updated,
        "error": result.error,
    }


@shared_task
def ingest_api_sources() -> dict:
    now = timezone.now()
    due_sources = Source.objects.filter(type=SourceType.API, is_active=True)
    queued = 0
    for source in due_sources:
        if source_is_due(source, now=now):
            ingest_source_task.delay(source.id)
            queued += 1
    return {"queued": queued, "source_type": "API"}


@shared_task
def ingest_company_sources() -> dict:
    now = timezone.now()
    due_sources = Source.objects.filter(type__in=[SourceType.COMPANY, SourceType.SCRAPER], is_active=True)
    queued = 0
    for source in due_sources:
        if source_is_due(source, now=now):
            ingest_source_task.delay(source.id)
            queued += 1
    return {"queued": queued, "source_type": "COMPANY_OR_SCRAPER"}
