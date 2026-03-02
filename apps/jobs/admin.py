from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "location", "job_type", "posted_at")
    list_filter = ("job_type", "location", "posted_at")
    search_fields = ("title", "location", "employer__username", "employer__email")
    autocomplete_fields = ("employer",)
