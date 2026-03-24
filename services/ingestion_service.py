from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from jobs.models import ApiFetchLog, Company, Job, Source, SourceType, build_job_dedupe_key
from services.job_aggregator import parse_iso_datetime, parse_salary_range
from services.search_service import index_job


DEFAULT_USER_AGENT = "JobPortalBot/1.0 (+https://example.com/contact)"


@dataclass
class IngestionResult:
    source_id: int
    source_name: str
    ok: bool
    created: int
    updated: int
    error: str = ""


def source_is_due(source: Source, *, now: datetime | None = None) -> bool:
    now = now or timezone.now()
    if source.last_fetched_at is None:
        return True
    return source.last_fetched_at + timedelta(minutes=max(1, source.frequency)) <= now


def _sleep_rate_limit() -> None:
    low = float(settings.INGESTION_MIN_DELAY_SECONDS)
    high = float(settings.INGESTION_MAX_DELAY_SECONDS)
    if high < low:
        low, high = high, low
    time.sleep(random.uniform(low, high))


def _safe_snippet(text: str, max_chars: int = 800) -> str:
    clean = (text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def _source_url(source: Source) -> str:
    endpoint = (source.endpoint or "").strip()
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return urljoin(source.base_url, endpoint)


def _headers(source: Source) -> dict[str, str]:
    base = {"User-Agent": DEFAULT_USER_AGENT}
    if isinstance(source.request_headers, dict):
        for key, value in source.request_headers.items():
            if key and value:
                base[str(key)] = str(value)
    return base


def _extract_path(payload: Any, path: str) -> Any:
    if not path:
        return payload
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
            continue
        if isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
            continue
        return None
    return current


def _can_fetch_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(DEFAULT_USER_AGENT, url)


def _parse_dt(value: str) -> datetime | None:
    parsed = parse_iso_datetime(value)
    if parsed.year <= 1:
        return None
    return parsed


def _normalize_job(source: Source, raw: dict[str, Any]) -> dict[str, Any] | None:
    title = str(raw.get("title") or "").strip()
    company_name = str(raw.get("company") or "").strip()
    location = str(raw.get("location") or "").strip()
    source_url = str(raw.get("source_url") or "").strip()
    if not title or not source_url:
        return None
    salary_text = str(raw.get("salary") or "")
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")
    if salary_min is None and salary_max is None and salary_text:
        salary_min, salary_max = parse_salary_range(salary_text)
    return {
        "title": title,
        "company_name": company_name,
        "location": location,
        "role": str(raw.get("role") or "").strip(),
        "experience": str(raw.get("experience") or "").strip(),
        "salary_min": int(salary_min) if isinstance(salary_min, (int, float)) else None,
        "salary_max": int(salary_max) if isinstance(salary_max, (int, float)) else None,
        "salary_currency": str(raw.get("salary_currency") or "").strip(),
        "description_snippet": _safe_snippet(str(raw.get("description_snippet") or "")),
        "source_url": source_url,
        "posted_at": _parse_dt(str(raw.get("posted_at") or "")),
        "source_external_id": str(raw.get("source_external_id") or "").strip(),
        "metadata": raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {},
    }


def _upsert_job(source: Source, normalized: dict[str, Any]) -> tuple[Job, bool]:
    company = None
    if normalized["company_name"]:
        company, _ = Company.objects.get_or_create(name=normalized["company_name"])
    dedupe_key = build_job_dedupe_key(
        title=normalized["title"],
        company=normalized["company_name"],
        location=normalized["location"],
    )
    defaults = {
        "title": normalized["title"],
        "company": company,
        "company_name": normalized["company_name"],
        "location": normalized["location"],
        "role": normalized["role"],
        "experience": normalized["experience"],
        "salary_min": normalized["salary_min"],
        "salary_max": normalized["salary_max"],
        "salary_currency": normalized["salary_currency"],
        "description_snippet": normalized["description_snippet"],
        "source": source,
        "source_url": normalized["source_url"],
        "source_external_id": normalized["source_external_id"],
        "posted_at": normalized["posted_at"],
        "is_active": True,
        "metadata": normalized["metadata"],
    }
    with transaction.atomic():
        job, created = Job.objects.update_or_create(dedupe_key=dedupe_key, defaults=defaults)
    index_job(job)
    return job, created


def _extract_api_jobs(source: Source, payload: Any) -> list[dict[str, Any]]:
    name = source.name.lower().strip()
    if "remotive" in name and isinstance(payload, dict):
        rows = payload.get("jobs", [])
        jobs: list[dict[str, Any]] = []
        if isinstance(rows, list):
            for item in rows:
                if not isinstance(item, dict):
                    continue
                jobs.append(
                    {
                        "title": item.get("title"),
                        "company": item.get("company_name"),
                        "location": item.get("candidate_required_location"),
                        "salary": item.get("salary"),
                        "description_snippet": item.get("description", ""),
                        "source_url": item.get("url"),
                        "posted_at": item.get("publication_date"),
                        "role": item.get("category", ""),
                        "source_external_id": item.get("id", ""),
                    }
                )
        return jobs

    if "arbeitnow" in name and isinstance(payload, dict):
        rows = payload.get("data", [])
        jobs: list[dict[str, Any]] = []
        if isinstance(rows, list):
            for item in rows:
                if not isinstance(item, dict):
                    continue
                jobs.append(
                    {
                        "title": item.get("title"),
                        "company": item.get("company_name"),
                        "location": item.get("location"),
                        "description_snippet": item.get("description", ""),
                        "source_url": item.get("url"),
                        "posted_at": item.get("created_at"),
                        "source_external_id": item.get("slug", ""),
                        "metadata": {"tags": item.get("tags", [])},
                    }
                )
        return jobs

    parser = source.parser_config if isinstance(source.parser_config, dict) else {}
    rows = _extract_path(payload, str(parser.get("results_path", "")))
    if not isinstance(rows, list):
        return []
    mapping = parser.get("mapping", {})
    if not isinstance(mapping, dict):
        mapping = {}

    jobs = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        job: dict[str, Any] = {}
        for target, source_path in mapping.items():
            if not isinstance(source_path, str):
                continue
            job[target] = _extract_path(row, source_path)
        jobs.append(job)
    return jobs


def ingest_api_source(source: Source) -> IngestionResult:
    started = time.perf_counter()
    if source.type != SourceType.API:
        return IngestionResult(source.id, source.name, ok=False, created=0, updated=0, error="invalid_source_type")
    url = _source_url(source)
    _sleep_rate_limit()
    created = 0
    updated = 0
    error = ""
    ok = True
    try:
        response = requests.get(url, headers=_headers(source), timeout=20)
        response.raise_for_status()
        payload = response.json()
        raw_jobs = _extract_api_jobs(source, payload)
        for raw in raw_jobs:
            normalized = _normalize_job(source, raw)
            if normalized is None:
                continue
            try:
                _, was_created = _upsert_job(source, normalized)
            except IntegrityError:
                continue
            if was_created:
                created += 1
            else:
                updated += 1
    except Exception as exc:
        ok = False
        error = str(exc)[:255]

    latency_ms = int((time.perf_counter() - started) * 1000)
    ApiFetchLog.objects.create(
        source=source.name[:30],
        ok=ok,
        latency_ms=latency_ms,
        error=error,
    )
    source.last_fetched_at = timezone.now()
    source.last_error = error
    source.save(update_fields=["last_fetched_at", "last_error", "updated_at"])
    return IngestionResult(source.id, source.name, ok=ok, created=created, updated=updated, error=error)


def _extract_company_jobs(source: Source, html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, Any]] = []

    for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not node.string:
            continue
        try:
            data = json.loads(node.string)
        except Exception:
            continue
        objects = data if isinstance(data, list) else [data]
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            kind = str(obj.get("@type") or "")
            if kind.lower() != "jobposting":
                continue
            identifier = obj.get("identifier", {})
            source_external_id = ""
            if isinstance(identifier, dict):
                source_external_id = str(identifier.get("value") or "")
            jobs.append(
                {
                    "title": obj.get("title"),
                    "company": obj.get("hiringOrganization", {}).get("name", "") if isinstance(obj.get("hiringOrganization"), dict) else "",
                    "location": obj.get("jobLocation", {}).get("address", {}).get("addressLocality", "") if isinstance(obj.get("jobLocation"), dict) else "",
                    "description_snippet": BeautifulSoup(str(obj.get("description") or ""), "html.parser").get_text(" ", strip=True),
                    "source_url": obj.get("url") or _source_url(source),
                    "posted_at": obj.get("datePosted"),
                    "source_external_id": source_external_id,
                    "metadata": {"employmentType": obj.get("employmentType", "")},
                }
            )

    if jobs:
        return jobs

    config = source.parser_config if isinstance(source.parser_config, dict) else {}
    card_selector = str(config.get("card_selector", "a[href]"))
    title_selector = str(config.get("title_selector", "")).strip()
    location_selector = str(config.get("location_selector", "")).strip()
    company_name = str(config.get("company_name", "")).strip()
    description_selector = str(config.get("description_selector", "")).strip()

    cards = soup.select(card_selector)
    for card in cards[:100]:
        href = card.get("href") if hasattr(card, "get") else None
        url = urljoin(source.base_url, href) if href else _source_url(source)
        if not url or "javascript:" in url.lower():
            continue
        if not title_selector:
            title = card.get_text(" ", strip=True)
        else:
            title_node = card.select_one(title_selector)
            title = title_node.get_text(" ", strip=True) if title_node else ""
        location = ""
        if location_selector:
            loc_node = card.select_one(location_selector)
            location = loc_node.get_text(" ", strip=True) if loc_node else ""
        description = ""
        if description_selector:
            desc_node = card.select_one(description_selector)
            description = desc_node.get_text(" ", strip=True) if desc_node else ""
        jobs.append(
            {
                "title": title,
                "company": company_name,
                "location": location,
                "description_snippet": description,
                "source_url": url,
                "posted_at": "",
            }
        )
    return jobs


def ingest_company_source(source: Source) -> IngestionResult:
    started = time.perf_counter()
    if source.type not in {SourceType.COMPANY, SourceType.SCRAPER}:
        return IngestionResult(source.id, source.name, ok=False, created=0, updated=0, error="invalid_source_type")
    url = _source_url(source)
    created = 0
    updated = 0
    error = ""
    ok = True
    if not _can_fetch_url(url):
        ok = False
        error = "robots_disallow"
    else:
        _sleep_rate_limit()
        try:
            response = requests.get(url, headers=_headers(source), timeout=20)
            response.raise_for_status()
            raw_jobs = _extract_company_jobs(source, response.text)
            for raw in raw_jobs:
                normalized = _normalize_job(source, raw)
                if normalized is None:
                    continue
                try:
                    _, was_created = _upsert_job(source, normalized)
                except IntegrityError:
                    continue
                if was_created:
                    created += 1
                else:
                    updated += 1
        except Exception as exc:
            ok = False
            error = str(exc)[:255]

    latency_ms = int((time.perf_counter() - started) * 1000)
    ApiFetchLog.objects.create(
        source=source.name[:30],
        ok=ok,
        latency_ms=latency_ms,
        error=error,
    )
    source.last_fetched_at = timezone.now()
    source.last_error = error
    source.save(update_fields=["last_fetched_at", "last_error", "updated_at"])
    return IngestionResult(source.id, source.name, ok=ok, created=created, updated=updated, error=error)
