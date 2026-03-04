from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import strip_tags
from django.db.utils import OperationalError, ProgrammingError

from services.job_aggregator import MIN_UTC, aggregate_jobs, parse_iso_datetime

from .forms import JobSearchForm
from .models import JobCache, SearchLog


RESULT_LIMIT = 60
RESULTS_PER_PAGE = 10


def _is_safe_external_url(raw_url: str) -> bool:
    try:
        parsed = urlparse(raw_url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _short_text(html: str, max_chars: int = 220) -> str:
    text = strip_tags(html or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _matches_optional(haystack: str, needle: str) -> bool:
    if not needle:
        return True
    return needle.lower() in (haystack or "").lower()


def search(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = JobSearchForm(request.POST)
        if form.is_valid():
            params = {k: v for k, v in form.cleaned_data.items() if v}
            return redirect(f"{request.path}?{urlencode(params, doseq=True)}")
    else:
        form = JobSearchForm(request.GET)

    jobs_page: list[dict[str, Any]] = []
    error_message = ""
    total_jobs = 0
    page_obj = None
    base_querystring = ""

    if request.method == "GET" and form.is_valid() and form.cleaned_data.get("keyword"):
        keyword = form.cleaned_data["keyword"]
        location = form.cleaned_data.get("location", "")
        company = form.cleaned_data.get("company", "")
        category = form.cleaned_data.get("category", "")
        sources = form.cleaned_data.get("sources") or ["remotive", "arbeitnow"]
        sort = form.cleaned_data.get("sort") or "relevance"
        min_salary = form.cleaned_data.get("min_salary")
        max_salary = form.cleaned_data.get("max_salary")

        ip = request.META.get("REMOTE_ADDR", "unknown")
        bucket = int(time.time() // 60)
        rl_key = f"rl:search:{ip}:{bucket}"
        count = int(cache.get(rl_key, 0)) + 1
        cache.set(rl_key, count, timeout=70)
        if count > settings.SEARCH_RATE_LIMIT_PER_MINUTE:
            error_message = "Too many searches in a short time. Please wait a minute and try again."
            context = {
                "form": form,
                "jobs": [],
                "error_message": error_message,
                "result_limit": RESULT_LIMIT,
                "total_jobs": 0,
                "page_obj": None,
                "base_querystring": "",
            }
            return render(request, "jobs/results.html", context)

        query_label = " | ".join(
            part
            for part in [
                keyword,
                f"Location: {location}" if location else "",
                f"Company: {company}" if company else "",
                f"Category: {category}" if category else "",
            ]
            if part
        )
        try:
            SearchLog.objects.create(
                query=query_label[:255],
                keyword=keyword,
                location=location,
                company=company,
                category=category,
            )
        except (OperationalError, ProgrammingError):
            pass

        aggregation = aggregate_jobs(
            keyword=keyword,
            location=location,
            category=category or None,
            sources=sources,
            per_source_limit=60,
            dedupe=True,
        )
        fetched = aggregation.jobs
        if aggregation.warnings:
            error_message = " ".join(aggregation.warnings)

        filtered: list[dict[str, Any]] = []
        for job in fetched:
            if not _matches_optional(job.get("company", ""), company):
                continue
            if not _matches_optional(job.get("location", ""), location):
                continue
            url = job.get("url") or ""
            if not _is_safe_external_url(url):
                continue

            published_at = parse_iso_datetime(str(job.get("publication_date") or ""))
            if published_at == MIN_UTC:
                published_at = None

            job_salary_min = job.get("salary_min")
            job_salary_max = job.get("salary_max")
            if min_salary is not None:
                if job_salary_max is None or int(job_salary_max) < int(min_salary):
                    continue
            if max_salary is not None:
                if job_salary_min is None or int(job_salary_min) > int(max_salary):
                    continue

            description_raw = job.get("description", "")
            filtered.append(
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "salary": job.get("salary", ""),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "short_description": _short_text(description_raw, max_chars=220),
                    "long_description": _short_text(description_raw, max_chars=800),
                    "url": url,
                    "publication_date": job.get("publication_date", ""),
                    "published_at": published_at,
                    "category": job.get("category", ""),
                    "source": job.get("source", ""),
                }
            )
            if len(filtered) >= RESULT_LIMIT:
                break

        if sort == "date":
            filtered.sort(
                key=lambda j: j.get("published_at") or parse_iso_datetime(j.get("publication_date") or ""),
                reverse=True,
            )
        elif sort == "source":
            filtered.sort(
                key=lambda j: j.get("published_at") or parse_iso_datetime(j.get("publication_date") or ""),
                reverse=True,
            )
            filtered.sort(key=lambda j: str(j.get("source") or ""))

        paginator = Paginator(filtered, RESULTS_PER_PAGE)
        page_obj = paginator.get_page(request.GET.get("page") or 1)
        jobs_page = list(page_obj.object_list)
        total_jobs = paginator.count

        query_params = request.GET.copy()
        query_params.pop("page", None)
        base_querystring = query_params.urlencode()

        try:
            for job in jobs_page:
                JobCache.objects.update_or_create(
                    apply_url=job["url"],
                    defaults={
                        "title": job["title"][:255],
                        "company": (job["company"] or "")[:255],
                        "location": (job["location"] or "")[:255],
                        "source": (job["source"] or "")[:30],
                        "published_at": job.get("published_at"),
                        "salary_text": (job.get("salary") or "")[:255],
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                    },
                )
        except (OperationalError, ProgrammingError):
            pass

    context = {
        "form": form,
        "jobs": jobs_page,
        "error_message": error_message,
        "result_limit": RESULT_LIMIT,
        "total_jobs": total_jobs,
        "page_obj": page_obj,
        "base_querystring": base_querystring,
    }
    return render(request, "jobs/results.html", context)
