from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.decorators import employer_required

from .filters import JobFilter
from .forms import JobForm
from .models import Job


def job_list(request):
    qs = Job.objects.select_related("employer").all()
    job_filter = JobFilter(request.GET, queryset=qs)
    return render(
        request,
        "jobs/job_list.html",
        {"filter": job_filter, "jobs": job_filter.qs},
    )


def job_detail(request, pk: int):
    job = get_object_or_404(Job.objects.select_related("employer"), pk=pk)
    return render(request, "jobs/job_detail.html", {"job": job})


@login_required
@employer_required
def employer_job_list(request):
    jobs = Job.objects.filter(employer=request.user).order_by("-posted_at")
    return render(request, "jobs/employer_job_list.html", {"jobs": jobs})


@login_required
@employer_required
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            messages.success(request, "Job posted.")
            return redirect("jobs:employer_jobs")
    else:
        form = JobForm()
    return render(request, "jobs/job_form.html", {"form": form, "mode": "create"})


@login_required
@employer_required
def job_edit(request, pk: int):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect("jobs:employer_jobs")
    else:
        form = JobForm(instance=job)
    return render(
        request,
        "jobs/job_form.html",
        {"form": form, "mode": "edit", "job": job},
    )


@login_required
@employer_required
def job_delete(request, pk: int):
    job = get_object_or_404(Job, pk=pk, employer=request.user)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("jobs:employer_jobs")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})

