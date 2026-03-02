from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import EmployerProfile, JobSeekerProfile, Role, User


def _apply_bootstrap(form: forms.Form) -> None:
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        elif isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
            widget.attrs.setdefault("class", "form-check-input")
        else:
            widget.attrs.setdefault("class", "form-control")


class EmployerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=255, required=True)
    company_description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "company_name", "company_description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = Role.EMPLOYER
        if commit:
            user.save()
            EmployerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "company_name": self.cleaned_data["company_name"],
                    "company_description": self.cleaned_data.get("company_description", ""),
                },
            )
        return user


class JobSeekerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    resume = forms.FileField(required=False)
    skills = forms.CharField(widget=forms.Textarea, required=False)
    experience = forms.CharField(widget=forms.Textarea, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "resume", "skills", "experience")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = Role.JOB_SEEKER
        if commit:
            user.save()
            profile, _ = JobSeekerProfile.objects.get_or_create(user=user)
            profile.skills = self.cleaned_data.get("skills", "")
            profile.experience = self.cleaned_data.get("experience", "")
            resume = self.cleaned_data.get("resume")
            if resume:
                profile.resume = resume
            profile.full_clean()
            profile.save()
        return user


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = ("resume", "skills", "experience")
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 4}),
            "experience": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = ("company_name", "company_description")
        widgets = {"company_description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)


class BootstrapAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        _apply_bootstrap(self)
