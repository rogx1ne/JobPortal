from __future__ import annotations

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def highlight(text: str, query: str) -> str:
    raw_text = str(text or "")
    raw_query = str(query or "").strip()
    if not raw_text or not raw_query:
        return raw_text

    tokens = [t for t in re.split(r"\s+", raw_query) if len(t) >= 2]
    if not tokens:
        return raw_text

    escaped = escape(raw_text)
    for token in sorted(set(tokens), key=len, reverse=True):
        pattern = re.compile(re.escape(token), flags=re.IGNORECASE)
        escaped = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", escaped)

    return mark_safe(escaped)

