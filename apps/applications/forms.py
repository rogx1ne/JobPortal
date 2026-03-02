from __future__ import annotations

from django import forms

from .models import Application, ApplicationStatus


class ApplicationCreateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("cover_letter", "resume")
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("status",)
        widgets = {"status": forms.Select(choices=ApplicationStatus.choices)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs.setdefault("class", "form-select")
