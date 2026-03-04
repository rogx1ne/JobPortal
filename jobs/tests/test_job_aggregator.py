from __future__ import annotations

from django.test import SimpleTestCase

from services.job_aggregator import MIN_UTC, parse_iso_datetime, parse_salary_range, rank_jobs


class JobAggregatorTests(SimpleTestCase):
    def test_rank_jobs_prefers_title_match(self) -> None:
        jobs = [
            {"title": "Frontend React Engineer", "description": "React role", "company": "X", "publication_date": ""},
            {"title": "Python Backend Developer Intern", "description": "Internship", "company": "Y", "publication_date": ""},
        ]
        ranked = rank_jobs(jobs, "python internship")
        self.assertEqual(ranked[0]["title"], "Python Backend Developer Intern")
        self.assertGreaterEqual(ranked[0]["score"], ranked[1]["score"])

    def test_parse_iso_datetime_handles_z_suffix(self) -> None:
        dt = parse_iso_datetime("2026-03-04T10:11:12Z")
        self.assertNotEqual(dt, MIN_UTC)
        self.assertIsNotNone(dt.tzinfo)

    def test_parse_iso_datetime_makes_naive_utc(self) -> None:
        dt = parse_iso_datetime("2026-03-04 10:11:12")
        self.assertIsNotNone(dt.tzinfo)

    def test_parse_salary_range_basic(self) -> None:
        self.assertEqual(parse_salary_range("$50k-$70k"), (50000, 70000))
        self.assertEqual(parse_salary_range("60000"), (60000, 60000))
        self.assertEqual(parse_salary_range(""), (None, None))
