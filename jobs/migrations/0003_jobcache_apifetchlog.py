from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0002_searchlog_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobcache",
            name="source",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="jobcache",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobcache",
            name="salary_text",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="jobcache",
            name="salary_min",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobcache",
            name="salary_max",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ApiFetchLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(db_index=True, max_length=30)),
                ("ok", models.BooleanField(db_index=True, default=True)),
                ("latency_ms", models.PositiveIntegerField(default=0)),
                ("error", models.CharField(blank=True, default="", max_length=255)),
                ("fetched_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-fetched_at"]},
        ),
    ]

