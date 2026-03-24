from django.contrib import admin

from .models import (
    ApiFetchLog,
    Application,
    Company,
    Job,
    JobCache,
    Profile,
    SavedJob,
    SearchLog,
    Source,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "headline", "updated_at")
    search_fields = ("user__username", "user__email", "full_name", "headline")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "website_url", "careers_url", "updated_at")
    search_fields = ("name", "website_url", "careers_url")


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "base_url", "endpoint", "frequency", "last_fetched_at", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name", "base_url", "endpoint")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company_name",
        "location",
        "experience",
        "salary_min",
        "salary_max",
        "source",
        "posted_at",
        "is_active",
    )
    list_filter = ("is_active", "source", "posted_at")
    search_fields = ("title", "company_name", "location", "role", "experience")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "job__title", "job__company_name")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "status", "applied_at", "updated_at")
    list_filter = ("status", "applied_at")
    search_fields = ("user__username", "job__title", "job__company_name", "notes")


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
