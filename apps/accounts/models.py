from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.validators import validate_resume_file

class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    EMPLOYER = "employer", "Employer"
    JOB_SEEKER = "job_seeker", "Job Seeker"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.JOB_SEEKER, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class EmployerProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="employer_profile",
        db_index=True,
    )
    company_name = models.CharField(max_length=255, db_index=True)
    company_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.company_name


def _resume_upload_to(instance: "JobSeekerProfile", filename: str) -> str:
    return f"resumes/profiles/user_{instance.user_id}/{filename}"


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="jobseeker_profile",
        db_index=True,
    )
    resume = models.FileField(
        upload_to=_resume_upload_to,
        blank=True,
        null=True,
        validators=[validate_resume_file],
    )
    skills = models.TextField(blank=True, default="")
    experience = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"JobSeekerProfile<{self.user_id}>"
