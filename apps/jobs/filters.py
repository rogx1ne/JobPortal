from __future__ import annotations

import django_filters

from .models import Job, JobType


class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        field_name="title", lookup_expr="icontains", label="Title"
    )
    location = django_filters.CharFilter(
        field_name="location", lookup_expr="icontains", label="Location"
    )
    job_type = django_filters.ChoiceFilter(choices=JobType.choices, label="Job type")

    class Meta:
        model = Job
        fields = ("q", "location", "job_type")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields["q"].widget.attrs.setdefault("class", "form-control")
        self.form.fields["location"].widget.attrs.setdefault("class", "form-control")
        self.form.fields["job_type"].widget.attrs.setdefault("class", "form-select")
