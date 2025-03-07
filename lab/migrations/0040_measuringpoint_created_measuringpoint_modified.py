# Generated by Django 5.0.7 on 2024-09-20 15:06

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0039_measuringpoint_measuringpoint_unique_name_per_run"),
    ]

    operations = [
        migrations.AddField(
            model_name="measuringpoint",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                help_text="Date this entry was first created",
                verbose_name="Created",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="measuringpoint",
            name="modified",
            field=models.DateTimeField(
                auto_now=True,
                help_text="Date this entry was most recently changed.",
                verbose_name="Modified",
            ),
        ),
    ]
