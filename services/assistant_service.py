from __future__ import annotations

import logging
import re
from typing import Any

from django.conf import settings
from django.db.models import Q

from jobs.models import Job, Profile
from services.search_service import hybrid_rank_jobs


logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-zA-Z0-9+#]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "to",
    "for",
    "in",
    "of",
    "with",
    "on",
    "at",
    "is",
    "are",
    "i",
    "me",
    "my",
    "you",
    "job",
    "jobs",
    "role",
    "roles",
    "please",
}


def _tokens(text: str) -> list[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    return [t for t in tokens if t and t not in _STOPWORDS]


def _detect_intent(message: str) -> str:
    text = (message or "").lower()
    if any(word in text for word in ["resume", "cv", "bullet", "summary", "ats"]):
        return "resume_help"
    if any(word in text for word in ["eligible", "eligibility", "qualify", "qualification", "fit for"]):
        return "eligibility_check"
    if any(word in text for word in ["find", "search", "recommend", "jobs", "internship", "role"]):
        return "job_discovery"
    return "general_guidance"


def _job_card(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "role": job.role,
        "experience": job.experience,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "source_url": job.source_url,
        "posted_at": job.posted_at,
    }


def _top_jobs_for_user(user, *, query: str = "", limit: int = 5) -> list[Job]:
    profile, _ = Profile.objects.get_or_create(user=user)
    skills = (profile.skills or "").strip()
    headline = (profile.headline or "").strip()

    search_text = query.strip()
    if not search_text:
        combined = " ".join(part for part in [headline, skills] if part).strip()
        search_text = combined

    queryset = Job.objects.filter(is_active=True)
    if search_text:
        token_clauses = Q()
        for token in _tokens(search_text)[:8]:
            token_clauses |= (
                Q(title__icontains=token)
                | Q(role__icontains=token)
                | Q(company_name__icontains=token)
                | Q(description_snippet__icontains=token)
            )
        queryset = queryset.filter(token_clauses) if token_clauses else queryset
    queryset = queryset.order_by("-posted_at", "-last_seen_at")[:300]
    ranked = hybrid_rank_jobs(jobs=queryset, query=search_text, limit=limit)
    return ranked


def _fallback_answer(
    *,
    intent: str,
    message: str,
    jobs: list[Job],
    selected_job: Job | None,
) -> str:
    if intent == "resume_help":
        return (
            "Focus your resume on measurable outcomes, role-specific keywords, and a concise professional summary. "
            "Tailor top bullets to the target role, keeping each bullet action-oriented and results-focused."
        )

    if intent == "eligibility_check":
        if selected_job:
            return (
                f"To evaluate fit for '{selected_job.title}', compare your skills and years of experience against the job's "
                "required role scope, tools, and location constraints. If gaps exist, address them with targeted projects and certifications."
            )
        return (
            "Eligibility checks are strongest when mapped directly to a specific role's required skills, experience, and location criteria. "
            "Share a target job for a tighter assessment."
        )

    if intent == "job_discovery":
        if jobs:
            return (
                "Based on your request, I shortlisted relevant roles below. Prioritize newer postings first, "
                "then optimize your resume toward the top 2-3 role patterns."
            )
        return "I could not find strong matches yet. Try adding specific skills, role names, and preferred location."

    return (
        "I can help with job discovery, resume suggestions, and eligibility analysis. "
        "Share a target role, skill set, or a specific job ID to get a focused response."
    )


def _build_system_prompt(intent: str) -> str:
    return (
        "You are a job search assistant. Keep responses practical and concise. "
        "Do not fabricate specific company hiring facts. "
        "Use only provided context and give actionable next steps. "
        f"Current intent: {intent}."
    )


def _build_user_prompt(
    *,
    message: str,
    profile: Profile,
    intent: str,
    jobs: list[Job],
    selected_job: Job | None,
) -> str:
    job_lines = []
    for job in jobs[:5]:
        job_lines.append(
            f"- [{job.id}] {job.title} | {job.company_name} | {job.location} | {job.source_url}"
        )
    selected_line = ""
    if selected_job:
        selected_line = (
            f"Selected job context: [{selected_job.id}] {selected_job.title} at {selected_job.company_name}, "
            f"location={selected_job.location}, role={selected_job.role}, exp={selected_job.experience}"
        )
    return (
        f"User message: {message}\n"
        f"Intent: {intent}\n"
        f"Profile headline: {profile.headline}\n"
        f"Profile skills: {profile.skills}\n"
        f"Profile bio: {profile.bio}\n"
        f"{selected_line}\n"
        "Recommended jobs:\n"
        + ("\n".join(job_lines) if job_lines else "- none")
        + "\nProvide:\n"
        "1) direct answer\n"
        "2) concise action plan\n"
        "3) mention any uncertainty."
    )


def _call_openai(*, system_prompt: str, user_prompt: str) -> str | None:
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
    except Exception:
        logger.warning("openai package unavailable for assistant")
        return None

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_output_tokens=500,
        )
    except Exception:
        logger.exception("assistant model call failed")
        return None

    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    return None


def _follow_ups_for_intent(intent: str) -> list[str]:
    if intent == "job_discovery":
        return [
            "Which location and salary range should I optimize for?",
            "Should I prioritize internships or full-time roles?",
        ]
    if intent == "resume_help":
        return [
            "Share your current resume summary for a tighter rewrite.",
            "Which role are you targeting so I can tailor keywords?",
        ]
    if intent == "eligibility_check":
        return [
            "Do you want a gap-by-gap skill match against this role?",
            "Should I suggest a 30-day preparation plan?",
        ]
    return ["Do you want role recommendations or resume help next?"]


def generate_assistant_reply(*, user, message: str, job_id: int | None = None) -> dict[str, Any]:
    profile, _ = Profile.objects.get_or_create(user=user)
    intent = _detect_intent(message)
    selected_job = None
    if job_id is not None:
        selected_job = Job.objects.filter(id=job_id, is_active=True).first()

    query_hint = message
    if intent == "resume_help":
        query_hint = " ".join([profile.skills or "", profile.headline or ""]).strip()
    recommended_jobs = _top_jobs_for_user(user, query=query_hint, limit=5)

    llm_answer = _call_openai(
        system_prompt=_build_system_prompt(intent),
        user_prompt=_build_user_prompt(
            message=message,
            profile=profile,
            intent=intent,
            jobs=recommended_jobs,
            selected_job=selected_job,
        ),
    )
    provider = "openai" if llm_answer else "rules"
    answer = llm_answer or _fallback_answer(
        intent=intent,
        message=message,
        jobs=recommended_jobs,
        selected_job=selected_job,
    )
    return {
        "intent": intent,
        "provider": provider,
        "answer": answer,
        "recommended_jobs": [_job_card(job) for job in recommended_jobs],
        "follow_up_questions": _follow_ups_for_intent(intent),
    }


def get_assistant_recommendations(*, user, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
    jobs = _top_jobs_for_user(user, query=query, limit=limit)
    return [_job_card(job) for job in jobs]
