from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class JobType(models.TextChoices):
    FULL_TIME = "full_time", "Full-time"
    PART_TIME = "part_time", "Part-time"
    INTERNSHIP = "internship", "Internship"


class Job(models.Model):
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs",
        db_index=True,
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=255, db_index=True)
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, db_index=True
    )
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_at"]
        indexes = [
            models.Index(fields=["title", "location"]),
            models.Index(fields=["job_type", "posted_at"]),
            models.Index(fields=["employer", "posted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.location})"

