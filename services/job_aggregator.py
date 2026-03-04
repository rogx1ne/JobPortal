from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 12
MIN_UTC = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class AggregationResult:
    jobs: list[dict[str, Any]]
    warnings: list[str]


class JobSourceError(RuntimeError):
    pass


def _cache_get(key: str) -> Any:
    try:
        from django.core.cache import cache
    except Exception:
        return None
    return cache.get(key)


def _cache_set(key: str, value: Any, *, ttl_seconds: int) -> None:
    try:
        from django.core.cache import cache
    except Exception:
        return
    cache.set(key, value, timeout=ttl_seconds)


def _record_api_fetch(*, source: str, ok: bool, latency_ms: int, error: str = "") -> None:
    try:
        from jobs.models import ApiFetchLog
    except Exception:
        return

    try:
        ApiFetchLog.objects.create(
            source=source[:30],
            ok=ok,
            latency_ms=max(0, int(latency_ms)),
            error=(error or "")[:255],
        )
    except Exception:
        return


_SALARY_NUM_RE = re.compile(r"(?P<num>\d+(?:[.,]\d+)?)\s*(?P<k>k)?", flags=re.IGNORECASE)


def parse_salary_range(text: str) -> tuple[int | None, int | None]:
    """
    Best-effort extraction from free-form salary strings like:
      - "$50k-$70k"
      - "50,000 - 70,000"
      - "€60k"
    """
    raw = (text or "").strip()
    if not raw:
        return None, None

    matches = []
    for m in _SALARY_NUM_RE.finditer(raw.replace(",", "")):
        num_s = m.group("num")
        if not num_s:
            continue
        try:
            num = float(num_s.replace(",", "").replace(" ", ""))
        except ValueError:
            continue
        if m.group("k"):
            num *= 1000
        value = int(num)
        if 0 < value < 10_000_000:
            matches.append(value)

    if not matches:
        return None, None

    if len(matches) == 1:
        return matches[0], matches[0]

    return min(matches), max(matches)


def rank_jobs(jobs: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    query = (query or "").strip().lower()
    if not query:
        for job in jobs:
            job["score"] = 0
        return jobs

    tokens = [t for t in re.split(r"\s+", query) if t]
    now = datetime.now(UTC)

    for job in jobs:
        score = 0
        title = str(job.get("title") or "").lower()
        description = str(job.get("description") or "").lower()
        company = str(job.get("company") or "").lower()

        if query in title:
            score += 10

        for token in tokens:
            if token in title:
                score += 5
            if token in description:
                score += 3
            if token in company:
                score += 1

        published_at = parse_iso_datetime(str(job.get("publication_date") or ""))
        if published_at != MIN_UTC:
            age = now - published_at
            if age <= timedelta(days=7):
                score += 2
            elif age <= timedelta(days=30):
                score += 1

        job["score"] = score

    jobs.sort(key=lambda j: int(j.get("score") or 0), reverse=True)
    return jobs


def _get_json(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    cache_key = f"api_json:{sha256(url.encode('utf-8')).hexdigest()}"
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    request = Request(url, headers={"User-Agent": "career-aggregator/1.0"})
    try:
        with urlopen(request, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                raise JobSourceError(f"HTTP {status}")
            body = resp.read().decode("utf-8")
    except (URLError, TimeoutError) as exc:
        raise JobSourceError("Network error") from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise JobSourceError("Invalid JSON") from exc

    if not isinstance(data, dict):
        raise JobSourceError("Unexpected payload")
    _cache_set(cache_key, data, ttl_seconds=600)
    return data


def fetch_remotive(*, keyword: str, category: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    base_url = "https://remotive.com/api/remote-jobs"
    params: dict[str, str] = {"search": keyword}
    if category:
        params["category"] = category

    payload = _get_json(f"{base_url}?{urlencode(params)}")
    raw_jobs = payload.get("jobs", [])
    if not isinstance(raw_jobs, list):
        return []

    jobs: list[dict[str, Any]] = []
    for job in raw_jobs[: max(1, limit)]:
        if not isinstance(job, dict):
            continue
        salary_text = job.get("salary", "") or ""
        salary_min, salary_max = parse_salary_range(salary_text)
        jobs.append(
            {
                "title": job.get("title", "") or "",
                "company": job.get("company_name", "") or "",
                "location": job.get("candidate_required_location", "") or "",
                "salary": salary_text,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "description": job.get("description", "") or "",
                "url": job.get("url", "") or "",
                "publication_date": job.get("publication_date", "") or "",
                "category": job.get("category", "") or "",
                "source": "Remotive",
            }
        )
    return jobs


def fetch_arbeitnow(*, keyword: str, category: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """
    Arbeitnow doesn't support server-side keyword search via query params.
    We fetch the latest page and filter locally by keyword (and optionally by tag/category).
    """
    base_url = "https://www.arbeitnow.com/api/job-board-api"
    payload = _get_json(base_url)
    raw_jobs = payload.get("data", [])
    if not isinstance(raw_jobs, list):
        return []

    keyword_lc = keyword.lower().strip()
    category_lc = (category or "").lower().strip()

    jobs: list[dict[str, Any]] = []
    for job in raw_jobs:
        if not isinstance(job, dict):
            continue

        title = job.get("title", "") or ""
        company = job.get("company_name", "") or ""
        location = job.get("location", "") or ""
        description = job.get("description", "") or ""
        url = job.get("url", "") or ""
        created_at = job.get("created_at", "") or ""
        tags = job.get("tags", []) or []

        haystack = f"{title}\n{company}\n{location}\n{description}".lower()
        if keyword_lc and keyword_lc not in haystack:
            continue

        if category_lc and isinstance(tags, list):
            tags_lc = {str(t).lower() for t in tags}
            if category_lc not in tags_lc:
                continue

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "salary": "",
                "salary_min": None,
                "salary_max": None,
                "description": description,
                "url": url,
                "publication_date": created_at,
                "category": "",
                "source": "Arbeitnow",
            }
        )

        if len(jobs) >= max(1, limit):
            break

    return jobs


def fetch_adzuna(*, keyword: str, location: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """
    Optional source. Requires env vars:
      - ADZUNA_APP_ID
      - ADZUNA_APP_KEY
      - ADZUNA_COUNTRY (default: us)
    """
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        return []

    country = os.getenv("ADZUNA_COUNTRY", "us").strip().lower() or "us"
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

    params: dict[str, str] = {
        "app_id": app_id,
        "app_key": app_key,
        "what": keyword,
        "results_per_page": str(max(1, min(limit, 50))),
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    payload = _get_json(f"{base_url}?{urlencode(params)}")
    raw_jobs = payload.get("results", [])
    if not isinstance(raw_jobs, list):
        return []

    jobs: list[dict[str, Any]] = []
    for job in raw_jobs[: max(1, limit)]:
        if not isinstance(job, dict):
            continue
        company = ""
        if isinstance(job.get("company"), dict):
            company = job["company"].get("display_name", "") or ""

        loc = ""
        if isinstance(job.get("location"), dict):
            loc = job["location"].get("display_name", "") or ""

        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        salary = ""
        if salary_min is not None or salary_max is not None:
            salary = f"{salary_min or ''} - {salary_max or ''}".strip(" -")

        jobs.append(
            {
                "title": job.get("title", "") or "",
                "company": company,
                "location": loc,
                "salary": salary,
                "salary_min": int(salary_min) if isinstance(salary_min, (int, float)) else None,
                "salary_max": int(salary_max) if isinstance(salary_max, (int, float)) else None,
                "description": job.get("description", "") or "",
                "url": job.get("redirect_url", "") or job.get("adref", "") or "",
                "publication_date": job.get("created", "") or "",
                "category": "",
                "source": "Adzuna",
            }
        )
    return jobs


def aggregate_jobs(
    *,
    keyword: str,
    location: str = "",
    category: str | None = None,
    sources: list[str] | None = None,
    per_source_limit: int = 50,
    dedupe: bool = True,
) -> AggregationResult:
    warnings: list[str] = []
    combined: list[dict[str, Any]] = []

    enabled = {s.strip().lower() for s in (sources or ["remotive", "arbeitnow", "adzuna"])}
    fetchers = []
    if "remotive" in enabled:
        fetchers.append(("Remotive", lambda: fetch_remotive(keyword=keyword, category=category, limit=per_source_limit)))
    if "arbeitnow" in enabled:
        fetchers.append(("Arbeitnow", lambda: fetch_arbeitnow(keyword=keyword, category=category, limit=per_source_limit)))
    if "adzuna" in enabled:
        fetchers.append(("Adzuna", lambda: fetch_adzuna(keyword=keyword, location=location, limit=per_source_limit)))

    for name, fn in fetchers:
        start = time.perf_counter()
        try:
            combined.extend(fn())
            _record_api_fetch(
                source=name,
                ok=True,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        except JobSourceError:
            warnings.append(f"{name} is temporarily unavailable.")
            _record_api_fetch(
                source=name,
                ok=False,
                latency_ms=int((time.perf_counter() - start) * 1000),
                error="fetch_failed",
            )

    if dedupe:
        unique: dict[str, dict[str, Any]] = {}
        for job in combined:
            url = str(job.get("url") or "").strip()
            if url:
                unique.setdefault(url, job)
        combined = list(unique.values())

    combined = rank_jobs(combined, keyword)
    return AggregationResult(jobs=combined, warnings=warnings)


def parse_iso_datetime(value: str) -> datetime:
    raw = (value or "").strip()
    if not raw:
        return MIN_UTC
    # Normalize ISO "Z" timezone to "+00:00" for fromisoformat.
    raw = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return MIN_UTC

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def get_trending_jobs(*, limit: int = 10, per_source_limit: int = 50) -> AggregationResult:
    """
    Fetches a small set of recent jobs for the homepage (no keyword required).
    """
    warnings: list[str] = []
    combined: list[dict[str, Any]] = []

    for name, fn in [
        ("Remotive", lambda: fetch_remotive(keyword="", category=None, limit=per_source_limit)),
        ("Arbeitnow", lambda: fetch_arbeitnow(keyword="", category=None, limit=per_source_limit)),
    ]:
        start = time.perf_counter()
        try:
            combined.extend(fn())
            _record_api_fetch(
                source=name,
                ok=True,
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        except JobSourceError:
            warnings.append(f"{name} is temporarily unavailable.")
            _record_api_fetch(
                source=name,
                ok=False,
                latency_ms=int((time.perf_counter() - start) * 1000),
                error="fetch_failed",
            )

    unique: dict[str, dict[str, Any]] = {}
    for job in combined:
        url = str(job.get("url") or "").strip()
        if url:
            unique.setdefault(url, job)
    jobs = list(unique.values())

    jobs.sort(key=lambda j: parse_iso_datetime(str(j.get("publication_date") or "")), reverse=True)
    return AggregationResult(jobs=jobs[: max(1, limit)], warnings=warnings)
