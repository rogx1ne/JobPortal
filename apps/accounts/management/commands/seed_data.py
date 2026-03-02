from __future__ import annotations

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction

from apps.accounts.models import EmployerProfile, JobSeekerProfile, Role, User
from apps.applications.models import Application, ApplicationStatus
from apps.jobs.models import Job, JobType


class Command(BaseCommand):
    help = "Seed sample Job Portal data (idempotent; safe for dev environments)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = _upsert_user(
            username="admin",
            email="admin@example.com",
            role=Role.ADMIN,
            password="Admin123!Admin123!",
            is_staff=True,
            is_superuser=True,
        )

        employer1 = _upsert_user(
            username="employer1",
            email="employer1@example.com",
            role=Role.EMPLOYER,
            password="Employer123!Employer123!",
        )
        EmployerProfile.objects.update_or_create(
            user=employer1,
            defaults={
                "company_name": "Acme Hiring",
                "company_description": "We build products people love.",
            },
        )

        employer2 = _upsert_user(
            username="employer2",
            email="employer2@example.com",
            role=Role.EMPLOYER,
            password="Employer123!Employer123!",
        )
        EmployerProfile.objects.update_or_create(
            user=employer2,
            defaults={
                "company_name": "Globex Careers",
                "company_description": "Join our fast-growing team.",
            },
        )

        seeker1 = _upsert_user(
            username="seeker1",
            email="seeker1@example.com",
            role=Role.JOB_SEEKER,
            password="Seeker123!Seeker123!",
        )
        seeker2 = _upsert_user(
            username="seeker2",
            email="seeker2@example.com",
            role=Role.JOB_SEEKER,
            password="Seeker123!Seeker123!",
        )

        _upsert_jobseeker_profile(seeker1, skills="Python, Django, MySQL", experience="2 years backend development.")
        _upsert_jobseeker_profile(seeker2, skills="Java, Spring, SQL", experience="1 year internship + projects.")

        job1 = _upsert_job(
            employer=employer1,
            title="Backend Developer (Django)",
            location="New York",
            job_type=JobType.FULL_TIME,
            description="Build and maintain Django services and templates.",
        )
        job2 = _upsert_job(
            employer=employer1,
            title="QA Intern",
            location="Remote",
            job_type=JobType.INTERNSHIP,
            description="Help test new features and write test plans.",
        )
        job3 = _upsert_job(
            employer=employer2,
            title="Part-time Support Engineer",
            location="Austin",
            job_type=JobType.PART_TIME,
            description="Assist customers and triage bug reports.",
        )

        _upsert_application(job=job1, applicant=seeker1, status=ApplicationStatus.APPLIED)
        _upsert_application(job=job2, applicant=seeker2, status=ApplicationStatus.SHORTLISTED)
        _upsert_application(job=job3, applicant=seeker1, status=ApplicationStatus.REJECTED)

        self.stdout.write(self.style.SUCCESS("Job Portal seed data created/updated."))


def _upsert_user(
    *,
    username: str,
    email: str,
    role: str,
    password: str,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "is_active": True,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    dirty = False
    if user.email != email:
        user.email = email
        dirty = True
    if user.role != role:
        user.role = role
        dirty = True
    if user.is_staff != is_staff:
        user.is_staff = is_staff
        dirty = True
    if user.is_superuser != is_superuser:
        user.is_superuser = is_superuser
        dirty = True
    if not user.is_active:
        user.is_active = True
        dirty = True

    if created or not user.check_password(password):
        user.set_password(password)
        dirty = True

    if dirty:
        user.save()
    return user


def _fake_pdf(name: str = "resume.pdf") -> ContentFile:
    return ContentFile(b"%PDF-1.4\n% Job Portal seed resume\n", name=name)


def _upsert_jobseeker_profile(user: User, *, skills: str, experience: str) -> JobSeekerProfile:
    profile, _ = JobSeekerProfile.objects.get_or_create(user=user)
    changed = False
    if profile.skills != skills:
        profile.skills = skills
        changed = True
    if profile.experience != experience:
        profile.experience = experience
        changed = True
    if not profile.resume:
        profile.resume.save("resume.pdf", _fake_pdf(), save=False)
        changed = True
    if changed:
        profile.save()
    return profile


def _upsert_job(
    *,
    employer: User,
    title: str,
    location: str,
    job_type: str,
    description: str,
) -> Job:
    job, _ = Job.objects.get_or_create(
        employer=employer,
        title=title,
        defaults={
            "location": location,
            "job_type": job_type,
            "description": description,
        },
    )
    dirty = False
    for field, val in {
        "location": location,
        "job_type": job_type,
        "description": description,
    }.items():
        if getattr(job, field) != val:
            setattr(job, field, val)
            dirty = True
    if dirty:
        job.save()
    return job


def _upsert_application(*, job: Job, applicant: User, status: str) -> Application:
    app, created = Application.objects.get_or_create(
        job=job,
        applicant=applicant,
        defaults={
            "cover_letter": "Excited to apply. Please consider my application.",
            "status": status,
            "resume": _fake_pdf("application_resume.pdf"),
        },
    )
    dirty = False
    if app.status != status:
        app.status = status
        dirty = True
    if not app.resume:
        app.resume.save("application_resume.pdf", _fake_pdf("application_resume.pdf"), save=False)
        dirty = True
    if created or dirty:
        app.save()
    return app
