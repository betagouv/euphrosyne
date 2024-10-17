# Generated by Django 5.0.7 on 2024-10-02 11:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0041_runobjectgroup_alter_run_run_object_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="RunObjetGroupImage",
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
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date this entry was first created",
                        verbose_name="Created",
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Date this entry was most recently changed.",
                        verbose_name="Modified",
                    ),
                ),
                ("path", models.CharField(max_length=256, verbose_name="Path")),
                (
                    "transform",
                    models.JSONField(null=True, verbose_name="Image transformation"),
                ),
                (
                    "run_object_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="lab.runobjectgroup",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]