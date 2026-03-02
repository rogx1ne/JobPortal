from __future__ import annotations

import os

from django.core.exceptions import ValidationError


ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def validate_resume_file(file) -> None:
    ext = os.path.splitext(getattr(file, "name", "") or "")[1].lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise ValidationError("Resume must be a PDF or Word document (pdf/doc/docx).")

    size = getattr(file, "size", None)
    if size is not None and size > MAX_RESUME_SIZE_BYTES:
        raise ValidationError("Resume file size must be 5MB or less.")
