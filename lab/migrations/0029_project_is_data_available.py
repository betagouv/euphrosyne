# Generated by Django 4.2.6 on 2023-10-27 15:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lab", "0028_alter_objectgroup_dating"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="is_data_available",
            field=models.BooleanField(
                default=False,
                help_text="Has at least one run with data available.",
                verbose_name="Data available",
            ),
        ),
    ]