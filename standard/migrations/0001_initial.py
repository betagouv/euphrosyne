# Generated by Django 5.1.1 on 2024-11-12 14:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("lab", "0040_merge_20241024_1024"),
    ]

    operations = [
        migrations.CreateModel(
            name="Standard",
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
                ("label", models.CharField(max_length=255, verbose_name="Label")),
            ],
            options={
                "verbose_name": "Standard",
                "verbose_name_plural": "Standards",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("label",), name="unique_standard_label"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="MeasuringPointStandard",
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
                    "measuring_point",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="standard",
                        to="lab.measuringpoint",
                    ),
                ),
                (
                    "standard",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="measuring_points",
                        to="standard.standard",
                    ),
                ),
            ],
            options={
                "verbose_name": "Measuring Point Standard",
                "verbose_name_plural": "Measuring Point Standards",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("standard", "measuring_point"),
                        name="unique_measuring_point_standard",
                    )
                ],
            },
        ),
    ]