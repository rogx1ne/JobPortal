from __future__ import annotations

import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "career_aggregator.settings")

app = Celery("career_aggregator")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
