from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchlog",
            name="keyword",
            field=models.CharField(blank=True, db_index=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="searchlog",
            name="location",
            field=models.CharField(blank=True, db_index=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="searchlog",
            name="company",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="searchlog",
            name="category",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]

