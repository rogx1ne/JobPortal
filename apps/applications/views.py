from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import employer_required, job_seeker_required
from apps.jobs.models import Job

from .forms import ApplicationCreateForm, ApplicationStatusForm
from .models import Application


@login_required
@job_seeker_required
def apply_to_job(request, job_id: int):
    job = get_object_or_404(Job, pk=job_id)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You have already applied to this job.")
        return redirect("applications:my_applications")

    if request.method == "POST":
        form = ApplicationCreateForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            try:
                with transaction.atomic():
                    application.save()
            except IntegrityError:
                messages.warning(request, "You have already applied to this job.")
                return redirect("applications:my_applications")
            messages.success(request, "Application submitted.")
            return redirect("applications:my_applications")
    else:
        form = ApplicationCreateForm()

    return render(request, "applications/apply.html", {"job": job, "form": form})


@login_required
@job_seeker_required
def my_applications(request):
    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job", "job__employer")
        .order_by("-applied_at")
    )
    return render(
        request, "applications/my_applications.html", {"applications": applications}
    )


@login_required
@employer_required
def job_applicants(request, job_id: int):
    job = get_object_or_404(Job, pk=job_id, employer=request.user)
    applications = (
        Application.objects.filter(job=job)
        .select_related("applicant")
        .order_by("-applied_at")
    )
    for a in applications:
        a.status_form = ApplicationStatusForm(instance=a)
    return render(
        request,
        "applications/job_applicants.html",
        {"job": job, "applications": applications},
    )


@login_required
@employer_required
def update_application_status(request, application_id: int):
    application = get_object_or_404(
        Application.objects.select_related("job"),
        pk=application_id,
        job__employer=request.user,
    )
    if request.method != "POST":
        return redirect("applications:job_applicants", job_id=application.job_id)

    form = ApplicationStatusForm(request.POST, instance=application)
    if form.is_valid():
        form.save()
        messages.success(request, "Application status updated.")
    else:
        messages.error(request, "Invalid status update.")
    return redirect("applications:job_applicants", job_id=application.job_id)
