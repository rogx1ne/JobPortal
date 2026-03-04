from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SearchLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="JobCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("company", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("apply_url", models.URLField(max_length=500, unique=True)),
                ("fetched_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-fetched_at"]},
        ),
    ]

