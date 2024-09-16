# Generated by Django 5.0.7 on 2024-09-09 13:57

import lab.methods.model_fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0037_remove_period_period_unique_label_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="run",
            name="filters_for_detector_HE1",
            field=lab.methods.model_fields.FiltersCharField(
                "PIXE",
                "HE1",
                [
                    "100 µm Be",
                    "100 µm Mylar",
                    "200 µm Mylar",
                    "50 µm Al",
                    "100 µm Al",
                    "150 µm Al",
                    "200 µm Al",
                    "13 µm Cr + 50 µm Al",
                    "50 µm Cu",
                    "75 µm Cu",
                    "25µm Co",
                    "_",
                ],
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="filters_for_detector_HE2",
            field=lab.methods.model_fields.FiltersCharField(
                "PIXE",
                "HE2",
                [
                    "100 µm Be",
                    "100 µm Mylar",
                    "200 µm Mylar",
                    "50 µm Al",
                    "100 µm Al",
                    "150 µm Al",
                    "200 µm Al",
                    "13 µm Cr + 50 µm Al",
                    "50 µm Cu",
                    "75 µm Cu",
                    "25µm Co",
                    "_",
                ],
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="filters_for_detector_HE3",
            field=lab.methods.model_fields.FiltersCharField(
                "PIXE",
                "HE3",
                [
                    "100 µm Be",
                    "100 µm Mylar",
                    "200 µm Mylar",
                    "50 µm Al",
                    "100 µm Al",
                    "150 µm Al",
                    "200 µm Al",
                    "13 µm Cr + 50 µm Al",
                    "50 µm Cu",
                    "75 µm Cu",
                    "25µm Co",
                    "_",
                ],
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="filters_for_detector_HE4",
            field=lab.methods.model_fields.FiltersCharField(
                "PIXE",
                "HE4",
                [
                    "100 µm Be",
                    "100 µm Mylar",
                    "200 µm Mylar",
                    "50 µm Al",
                    "100 µm Al",
                    "150 µm Al",
                    "200 µm Al",
                    "13 µm Cr + 50 µm Al",
                    "50 µm Cu",
                    "75 µm Cu",
                    "25µm Co",
                    "_",
                ],
            ),
        ),
    ]