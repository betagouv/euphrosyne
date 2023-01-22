# Generated by Django 4.1.5 on 2023-01-22 08:37

from slugify import slugify

from django.db import migrations, models
from lab.models import Project


def gen_slug(apps, _):
    # pylint: disable=invalid-name
    ProjectModel: Project = apps.get_model("lab", "Project")
    for row in ProjectModel.objects.all():
        new_slug = slugify(row.name)
        similar_slug_count = ProjectModel.objects.filter(slug=new_slug).count()
        # add '-{count}' to slug to prevent unique collision.
        if similar_slug_count:
            new_slug = f"{new_slug}-{similar_slug_count}"
        row.slug = new_slug
        row.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0025_alter_institution_country_alter_institution_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="slug",
            field=models.CharField(
                max_length=255,
                null=True,
                verbose_name="Project name slug",
            ),
        ),
        migrations.RunPython(gen_slug, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="slug",
            field=models.CharField(
                max_length=255,
                null=False,
                unique=True,
                verbose_name="Project name slug",
            ),
        ),
    ]
