# Generated by Django 5.0.1 on 2024-02-12 11:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lab", "0031_project_confidential"),
    ]

    operations = [
        migrations.AlterField(
            model_name="participation",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="lab.project"
            ),
        ),
    ]
