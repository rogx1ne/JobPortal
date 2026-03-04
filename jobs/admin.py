from django.contrib import admin

from .models import ApiFetchLog, JobCache, SearchLog


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ("keyword", "location", "company", "category", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("keyword", "location", "company", "category", "query")


@admin.register(JobCache)
class JobCacheAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "location",
        "source",
        "published_at",
        "salary_text",
        "apply_url",
        "fetched_at",
    )
    list_filter = ("fetched_at",)
    search_fields = ("title", "company", "location", "source", "salary_text", "apply_url")


@admin.register(ApiFetchLog)
class ApiFetchLogAdmin(admin.ModelAdmin):
    list_display = ("source", "ok", "latency_ms", "error", "fetched_at")
    list_filter = ("source", "ok", "fetched_at")
    search_fields = ("source", "error")
