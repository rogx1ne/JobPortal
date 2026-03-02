from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.validators import validate_resume_file

def _application_resume_upload_to(instance: "Application", filename: str) -> str:
    return (
        f"resumes/applications/job_{instance.job_id}/user_{instance.applicant_id}/{filename}"
    )


class ApplicationStatus(models.TextChoices):
    APPLIED = "applied", "Applied"
    SHORTLISTED = "shortlisted", "Shortlisted"
    REJECTED = "rejected", "Rejected"


class Application(models.Model):
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="applications", db_index=True
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        db_index=True,
    )
    cover_letter = models.TextField(blank=True, default="")
    resume = models.FileField(
        upload_to=_application_resume_upload_to, validators=[validate_resume_file]
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED,
        db_index=True,
    )
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "applicant"], name="uniq_application_job_applicant"
            )
        ]
        indexes = [
            models.Index(fields=["applicant", "applied_at"]),
            models.Index(fields=["job", "applied_at"]),
            models.Index(fields=["status", "applied_at"]),
        ]

    def __str__(self) -> str:
        return f"Application<{self.job_id}:{self.applicant_id}>"
