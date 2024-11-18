# Generated by Django 5.0.6 on 2024-06-11 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "lab",
            "0038_alter_run_filters_for_detector_he1_and_more",
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="location",
            constraint=models.UniqueConstraint(
                fields=("geonames_id",), name="unique_geonames_id"
            ),
        ),
    ]
