from __future__ import annotations

import re

from django import forms


_SAFE_TEXT_RE = re.compile(r"^[\w\s\-\.\,\+\#\/\(\)]+$", flags=re.UNICODE)
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9\-]+$", flags=re.IGNORECASE)


class JobSearchForm(forms.Form):
    keyword = forms.CharField(
        max_length=80,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Python Developer",
                "autocomplete": "off",
            }
        ),
    )
    location = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional location (e.g. United States)",
                "autocomplete": "off",
            }
        ),
    )
    company = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional company filter",
                "autocomplete": "off",
            }
        ),
    )
    category = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional category (e.g. software-dev)",
                "autocomplete": "off",
            }
        ),
        help_text="Remotive category slug (e.g. software-dev).",
    )
    sources = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("remotive", "Remotive"),
            ("arbeitnow", "Arbeitnow"),
            ("adzuna", "Adzuna"),
        ],
        initial=["remotive", "arbeitnow"],
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        help_text="Choose which job sources to aggregate.",
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("relevance", "Relevance"),
            ("date", "Newest"),
            ("source", "Source"),
        ],
        initial="relevance",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_salary = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Min"}),
    )
    max_salary = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Max"}),
    )

    def clean_keyword(self) -> str:
        keyword = (self.cleaned_data.get("keyword") or "").strip()
        if len(keyword) < 2:
            raise forms.ValidationError("Please enter at least 2 characters.")
        if not _SAFE_TEXT_RE.match(keyword):
            raise forms.ValidationError("Keyword contains unsupported characters.")
        return keyword

    def clean_location(self) -> str:
        location = (self.cleaned_data.get("location") or "").strip()
        if location and not _SAFE_TEXT_RE.match(location):
            raise forms.ValidationError("Location contains unsupported characters.")
        return location

    def clean_company(self) -> str:
        company = (self.cleaned_data.get("company") or "").strip()
        if company and not _SAFE_TEXT_RE.match(company):
            raise forms.ValidationError("Company contains unsupported characters.")
        return company

    def clean_category(self) -> str:
        category = (self.cleaned_data.get("category") or "").strip()
        if category and not _SAFE_SLUG_RE.match(category):
            raise forms.ValidationError("Category should be a slug like 'software-dev'.")
        return category

    def clean_sources(self) -> list[str]:
        sources = self.cleaned_data.get("sources") or []
        allowed = {"remotive", "arbeitnow", "adzuna"}
        return [s for s in sources if s in allowed]

    def clean(self):
        cleaned = super().clean()
        min_salary = cleaned.get("min_salary")
        max_salary = cleaned.get("max_salary")
        if min_salary is not None and max_salary is not None and min_salary > max_salary:
            self.add_error("max_salary", "Max salary must be greater than or equal to min salary.")
        return cleaned
