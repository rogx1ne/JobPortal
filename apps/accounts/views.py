from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .decorators import employer_required, job_seeker_required
from .forms import (
    EmployerProfileForm,
    EmployerSignUpForm,
    JobSeekerProfileForm,
    JobSeekerSignUpForm,
)


def register(request):
    return render(request, "accounts/register.html")


def register_employer(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = EmployerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Employer account created.")
            return redirect("core:dashboard")
    else:
        form = EmployerSignUpForm()

    return render(request, "accounts/register_employer.html", {"form": form})


def register_job_seeker(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = JobSeekerSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Job seeker account created.")
            return redirect("core:dashboard")
    else:
        form = JobSeekerSignUpForm()

    return render(request, "accounts/register_jobseeker.html", {"form": form})


@login_required
@job_seeker_required
def job_seeker_profile(request):
    profile = request.user.jobseeker_profile
    if request.method == "POST":
        form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect(reverse("accounts:jobseeker_profile"))
    else:
        form = JobSeekerProfileForm(instance=profile)
    return render(request, "accounts/jobseeker_profile.html", {"form": form})


@login_required
@employer_required
def employer_profile(request):
    profile = request.user.employer_profile
    if request.method == "POST":
        form = EmployerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated.")
            return redirect(reverse("accounts:employer_profile"))
    else:
        form = EmployerProfileForm(instance=profile)
    return render(request, "accounts/employer_profile.html", {"form": form})
