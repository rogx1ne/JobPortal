from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.accounts.decorators import employer_required, job_seeker_required
from apps.accounts.models import Role
from apps.applications.models import Application
from apps.jobs.models import Job


def home(request):
    latest_jobs = Job.objects.select_related("employer").all()[:6]
    return render(request, "core/home.html", {"latest_jobs": latest_jobs})


@login_required
def dashboard(request):
    user = request.user
    if user.is_superuser or user.role == Role.ADMIN:
        return redirect(reverse("admin:index"))
    if user.role == Role.EMPLOYER:
        return redirect("core:employer_dashboard")
    return redirect("core:jobseeker_dashboard")


@login_required
@employer_required
def employer_dashboard(request):
    jobs = (
        Job.objects.filter(employer=request.user)
        .annotate(applicant_count=Count("applications"))
        .order_by("-posted_at")
    )
    return render(request, "core/employer_dashboard.html", {"jobs": jobs})


@login_required
@job_seeker_required
def jobseeker_dashboard(request):
    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job", "job__employer")
        .order_by("-applied_at")[:10]
    )
    return render(
        request, "core/jobseeker_dashboard.html", {"applications": applications}
    )

