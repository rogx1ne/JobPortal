from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Count, Max
from django.db.utils import OperationalError, ProgrammingError
from urllib.parse import urlencode

from services.job_aggregator import get_trending_jobs

from jobs.forms import JobSearchForm
from jobs.models import SearchLog


def home(request: HttpRequest) -> HttpResponse:
    form = JobSearchForm()
    trending = get_trending_jobs(limit=10, per_source_limit=60)

    popular_searches = []
    try:
        popular_rows = (
            SearchLog.objects.exclude(keyword="")
            .values("keyword", "location", "company", "category")
            .annotate(count=Count("id"), last_seen=Max("timestamp"))
            .order_by("-count", "-last_seen")[:5]
        )
        for row in popular_rows:
            params = {
                "keyword": row.get("keyword") or "",
                "location": row.get("location") or "",
                "company": row.get("company") or "",
                "category": row.get("category") or "",
            }
            params = {k: v for k, v in params.items() if v}
            label = " | ".join(
                part
                for part in [
                    row.get("keyword") or "",
                    f"Location: {row.get('location')}" if row.get("location") else "",
                ]
                if part
            )
            popular_searches.append(
                {
                    "label": label,
                    "url": f"/search/?{urlencode(params)}",
                    "count": row.get("count", 0),
                }
            )
    except (OperationalError, ProgrammingError):
        popular_searches = []

    return render(
        request,
        "core/home.html",
        {
            "form": form,
            "trending_jobs": trending.jobs,
            "trending_warnings": trending.warnings,
            "popular_searches": popular_searches,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "core/about.html")
