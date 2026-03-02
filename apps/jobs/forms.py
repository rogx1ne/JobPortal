from __future__ import annotations

from django import forms

from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = (
            "title",
            "description",
            "location",
            "salary_min",
            "salary_max",
            "job_type",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        min_salary = cleaned.get("salary_min")
        max_salary = cleaned.get("salary_max")
        if min_salary is not None and max_salary is not None and min_salary > max_salary:
            self.add_error("salary_max", "Salary max must be greater than or equal to salary min.")
        return cleaned
