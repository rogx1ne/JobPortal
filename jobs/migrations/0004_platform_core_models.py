from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0003_jobcache_apifetchlog"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("website_url", models.URLField(blank=True, default="", max_length=500)),
                ("careers_url", models.URLField(blank=True, default="", max_length=500)),
                ("location", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Source",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "type",
                    models.CharField(
                        choices=[("API", "API"), ("SCRAPER", "Scraper"), ("COMPANY", "Company")], max_length=20
                    ),
                ),
                ("base_url", models.URLField(max_length=500)),
                ("endpoint", models.CharField(blank=True, default="", max_length=500)),
                ("frequency", models.PositiveIntegerField(default=120, help_text="Fetch frequency in minutes")),
                ("last_fetched_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("request_headers", models.JSONField(blank=True, default=dict)),
                ("parser_config", models.JSONField(blank=True, default=dict)),
                ("last_error", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, default="", max_length=255)),
                ("headline", models.CharField(blank=True, default="", max_length=255)),
                ("bio", models.TextField(blank=True, default="")),
                ("skills", models.CharField(blank=True, default="", max_length=500)),
                ("resume_url", models.URLField(blank=True, default="", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(db_index=True, max_length=255)),
                ("company_name", models.CharField(blank=True, db_index=True, default="", max_length=255)),
                ("role", models.CharField(blank=True, db_index=True, default="", max_length=120)),
                ("experience", models.CharField(blank=True, db_index=True, default="", max_length=120)),
                ("location", models.CharField(blank=True, db_index=True, default="", max_length=255)),
                ("salary_min", models.IntegerField(blank=True, null=True)),
                ("salary_max", models.IntegerField(blank=True, null=True)),
                ("salary_currency", models.CharField(blank=True, default="", max_length=10)),
                ("description_snippet", models.TextField(blank=True, default="")),
                ("source_url", models.URLField(max_length=500)),
                ("source_external_id", models.CharField(blank=True, default="", max_length=120)),
                ("posted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("dedupe_key", models.CharField(db_index=True, max_length=64, unique=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="jobs",
                        to="jobs.company",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="jobs",
                        to="jobs.source",
                    ),
                ),
            ],
            options={
                "ordering": ["-posted_at", "-last_seen_at"],
                "indexes": [
                    models.Index(fields=["title"], name="jobs_job_title_a19f54_idx"),
                    models.Index(fields=["location"], name="jobs_job_locatio_a3cd0f_idx"),
                    models.Index(fields=["role"], name="jobs_job_role_8f3d08_idx"),
                    models.Index(fields=["experience"], name="jobs_job_experie_4a77f6_idx"),
                    models.Index(fields=["posted_at"], name="jobs_job_posted__c10973_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SavedJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_by", to="jobs.job")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="saved_jobs", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("saved", "Saved"),
                            ("applied", "Applied"),
                            ("interview", "Interview"),
                            ("offer", "Offer"),
                            ("rejected", "Rejected"),
                        ],
                        default="applied",
                        max_length=20,
                    ),
                ),
                ("applied_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="jobs.job"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-applied_at"]},
        ),
        migrations.AddConstraint(
            model_name="job",
            constraint=models.UniqueConstraint(fields=("source", "source_url"), name="unique_source_url_per_source"),
        ),
        migrations.AddConstraint(
            model_name="savedjob",
            constraint=models.UniqueConstraint(fields=("user", "job"), name="unique_saved_job_per_user"),
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.UniqueConstraint(fields=("user", "job"), name="unique_application_per_user_job"),
        ),
    ]
