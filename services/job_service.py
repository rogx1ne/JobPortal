from __future__ import annotations

from typing import Any

from .job_aggregator import JobSourceError, fetch_remotive


class JobServiceError(RuntimeError):
    pass


def fetch_jobs(*, keyword: str, category: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """
    Backward-compatible Remotive-only fetcher.

    The project now uses `services/job_aggregator.py` for multi-source aggregation.
    """
    try:
        jobs = fetch_remotive(keyword=keyword, category=category, limit=limit)
    except JobSourceError as exc:
        raise JobServiceError("Unable to reach the job provider API. Please try again.") from exc

    normalized: list[dict[str, Any]] = []
    for job in jobs:
        normalized.append(
            {
                "title": job.get("title", "") or "",
                "company_name": job.get("company", "") or "",
                "candidate_required_location": job.get("location", "") or "",
                "salary": job.get("salary", "") or "",
                "description": job.get("description", "") or "",
                "url": job.get("url", "") or "",
                "publication_date": job.get("publication_date", "") or "",
                "category": job.get("category", "") or "",
            }
        )
    return normalized
