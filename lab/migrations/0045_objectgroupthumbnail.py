# Generated by Django 5.1.5 on 2025-02-03 14:53

import django.db.models.deletion
import lab.objects.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "lab",
            "0044_runobjetgroupimage_run_object_group_image_unique_path_transform_perrun_object_group",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="ObjectGroupThumbnail",
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
                    "image",
                    models.ImageField(
                        storage=lab.objects.models.get_thumbnail_storage,
                        upload_to=lab.objects.models.get_thumbnail_path,
                        verbose_name="Image",
                    ),
                ),
                (
                    "copyright",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Copyright"
                    ),
                ),
                (
                    "object_group",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="thumbnail",
                        to="lab.objectgroup",
                    ),
                ),
            ],
        ),
    ]
