from __future__ import annotations

from django.db import models


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
