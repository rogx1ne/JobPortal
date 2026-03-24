from __future__ import annotations

from hashlib import sha256

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


def build_job_dedupe_key(*, title: str, company: str, location: str) -> str:
    raw = "|".join(
        [
            (title or "").strip().lower(),
            (company or "").strip().lower(),
            (location or "").strip().lower(),
        ]
    )
    return sha256(raw.encode("utf-8")).hexdigest()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True, default="")
    headline = models.CharField(max_length=255, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    skills = models.CharField(max_length=500, blank=True, default="")
    resume_url = models.URLField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.full_name or self.user.get_username()


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    website_url = models.URLField(max_length=500, blank=True, default="")
    careers_url = models.URLField(max_length=500, blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SourceType(models.TextChoices):
    API = "API", "API"
    SCRAPER = "SCRAPER", "Scraper"
    COMPANY = "COMPANY", "Company"


class Source(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=20, choices=SourceType.choices)
    base_url = models.URLField(max_length=500)
    endpoint = models.CharField(max_length=500, blank=True, default="")
    frequency = models.PositiveIntegerField(default=120, help_text="Fetch frequency in minutes")
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    request_headers = models.JSONField(default=dict, blank=True)
    parser_config = models.JSONField(default=dict, blank=True)
    last_error = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"


class Job(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    company_name = models.CharField(max_length=255, db_index=True, blank=True, default="")
    role = models.CharField(max_length=120, blank=True, default="", db_index=True)
    experience = models.CharField(max_length=120, blank=True, default="", db_index=True)
    location = models.CharField(max_length=255, db_index=True, blank=True, default="")
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True, default="")
    description_snippet = models.TextField(blank=True, default="")
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    source_url = models.URLField(max_length=500)
    source_external_id = models.CharField(max_length=120, blank=True, default="")
    posted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    dedupe_key = models.CharField(max_length=64, unique=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-posted_at", "-last_seen_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["location"]),
            models.Index(fields=["role"]),
            models.Index(fields=["experience"]),
            models.Index(fields=["posted_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["source", "source_url"], name="unique_source_url_per_source")
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.company_name or (self.company.name if self.company else '')}"

    def save(self, *args, **kwargs) -> None:
        if not self.company_name and self.company:
            self.company_name = self.company.name
        if not self.dedupe_key:
            self.dedupe_key = build_job_dedupe_key(
                title=self.title,
                company=self.company_name,
                location=self.location,
            )
        super().save(*args, **kwargs)


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="unique_saved_job_per_user"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.job_id}"


class ApplicationStatus(models.TextChoices):
    SAVED = "saved", "Saved"
    APPLIED = "applied", "Applied"
    INTERVIEW = "interview", "Interview"
    OFFER = "offer", "Offer"
    REJECTED = "rejected", "Rejected"


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.APPLIED)
    applied_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="unique_application_per_user_job"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.job_id}:{self.status}"


class SearchLog(models.Model):
    query = models.CharField(max_length=255)
    keyword = models.CharField(max_length=80, blank=True, default="", db_index=True)
    location = models.CharField(max_length=80, blank=True, default="", db_index=True)
    company = models.CharField(max_length=80, blank=True, default="")
    category = models.CharField(max_length=40, blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        base = self.keyword or self.query
        return f"{base} @ {self.timestamp:%Y-%m-%d %H:%M}"


class JobCache(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    apply_url = models.URLField(max_length=500, unique=True)
    source = models.CharField(max_length=30, blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    salary_text = models.CharField(max_length=255, blank=True, default="")
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.company}"


class ApiFetchLog(models.Model):
    source = models.CharField(max_length=30, db_index=True)
    ok = models.BooleanField(default=True, db_index=True)
    latency_ms = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=255, blank=True, default="")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        status = "OK" if self.ok else "ERR"
        return f"{self.source} {status} ({self.latency_ms}ms)"
