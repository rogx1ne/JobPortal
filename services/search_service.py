from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable

from django.conf import settings
from django.utils import timezone

from jobs.models import Job


logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-zA-Z0-9+#]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "to",
    "for",
    "in",
    "of",
    "with",
    "on",
    "at",
    "is",
    "are",
    "job",
    "jobs",
    "internship",
    "internships",
    "role",
    "roles",
}


def _get_client():
    if not settings.MEILISEARCH_URL:
        return None
    try:
        import meilisearch
    except Exception:
        logger.warning("meilisearch package is unavailable")
        return None
    return meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY or None)


def _get_index():
    client = _get_client()
    if client is None:
        return None
    try:
        index = client.index(settings.MEILISEARCH_INDEX)
        index.update_filterable_attributes(["location", "role", "experience", "company_name"])
        return index
    except Exception:
        logger.exception("failed to access meilisearch index")
        return None


def serialize_job_document(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "role": job.role,
        "experience": job.experience,
        "description_snippet": job.description_snippet,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
    }


def index_job(job: Job) -> None:
    index = _get_index()
    if index is None:
        return
    try:
        index.add_documents([serialize_job_document(job)])
    except Exception:
        logger.exception("failed to index job %s", job.id)


def index_jobs(job_ids: list[int]) -> None:
    if not job_ids:
        return
    index = _get_index()
    if index is None:
        return
    jobs = Job.objects.filter(id__in=job_ids, is_active=True)
    payload = [serialize_job_document(job) for job in jobs]
    if not payload:
        return
    try:
        index.add_documents(payload)
    except Exception:
        logger.exception("failed to bulk index jobs")


def search_job_ids(query: str, limit: int = 100) -> list[int]:
    index = _get_index()
    if index is None:
        return []
    try:
        response = index.search(query, {"limit": limit})
        hits = response.get("hits", [])
    except Exception:
        logger.exception("meilisearch query failed")
        return []
    ids: list[int] = []
    for hit in hits:
        if isinstance(hit, dict) and isinstance(hit.get("id"), int):
            ids.append(hit["id"])
    return ids


def _tokenize(text: str) -> list[str]:
    tokens = [tok.lower() for tok in _TOKEN_RE.findall(text or "")]
    return [tok for tok in tokens if tok and tok not in _STOPWORDS]


def _text_score(job: Job, tokens: list[str], query: str) -> float:
    title = (job.title or "").lower()
    company = (job.company_name or "").lower()
    role = (job.role or "").lower()
    location = (job.location or "").lower()
    description = (job.description_snippet or "").lower()

    score = 0.0
    query_lc = (query or "").lower().strip()
    if query_lc and query_lc in title:
        score += 12
    if query_lc and query_lc in company:
        score += 5
    if query_lc and query_lc in role:
        score += 6

    for token in tokens:
        if token in title:
            score += 6
        if token in role:
            score += 4
        if token in company:
            score += 2
        if token in location:
            score += 1
        if token in description:
            score += 1.5
    return score


def _recency_score(job: Job) -> float:
    if not job.posted_at:
        return 0.0
    age = timezone.now() - job.posted_at
    if age <= timedelta(days=1):
        return 6.0
    if age <= timedelta(days=3):
        return 4.0
    if age <= timedelta(days=7):
        return 2.0
    if age <= timedelta(days=30):
        return 1.0
    return 0.0


def hybrid_rank_jobs(
    *,
    jobs: Iterable[Job],
    query: str = "",
    location: str = "",
    role: str = "",
    experience: str = "",
    limit: int = 100,
) -> list[Job]:
    candidate_jobs = list(jobs)
    if not candidate_jobs:
        return []

    tokens = _tokenize(query)
    meili_ids = search_job_ids(query, limit=max(limit, 100)) if query else []
    meili_order = {job_id: idx for idx, job_id in enumerate(meili_ids)}

    loc_lc = (location or "").lower().strip()
    role_lc = (role or "").lower().strip()
    exp_lc = (experience or "").lower().strip()

    scored: list[tuple[float, Job]] = []
    for job in candidate_jobs:
        score = _text_score(job, tokens, query) + _recency_score(job)

        if meili_order:
            if job.id in meili_order:
                score += max(0.0, 20.0 - (meili_order[job.id] * 0.25))
            else:
                score -= 3.0

        if loc_lc and loc_lc in (job.location or "").lower():
            score += 2.0
        if role_lc and role_lc in (job.role or "").lower():
            score += 2.0
        if exp_lc and exp_lc in (job.experience or "").lower():
            score += 2.0

        scored.append((score, job))

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].posted_at or datetime.min.replace(tzinfo=UTC),
            item[1].id,
        ),
        reverse=True,
    )
    return [job for _, job in scored[:limit]]
