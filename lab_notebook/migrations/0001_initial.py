# Generated by Django 5.0.7 on 2024-09-18 15:49

import django.db.models.deletion
from django.db import migrations, models


def add_run_notebook(apps, _):
    run_model = apps.get_model("lab", "Run")
    run_notebook_model = apps.get_model("lab_notebook", "RunNotebook")
    for run in run_model.objects.all():
        run_notebook_model.objects.create(run=run)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("lab", "0038_alter_run_filters_for_detector_he1_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RunNotebook",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("comments", models.TextField(blank=True, verbose_name="Comments")),
                (
                    "run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="run_notebook",
                        to="lab.run",
                        verbose_name="Run",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            code=add_run_notebook, reverse_code=migrations.RunPython.noop
        ),
    ]
