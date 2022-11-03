from django.db import connection, migrations, models

import shared.models

RAW_SQL_QUERY = """
SELECT 1 as id, name, country, COUNT(*) as duplicate_count
from lab_institution GROUP BY name, country
HAVING COUNT(*) > 1;
"""


def merge_duplicate_institutions(apps, _):
    inst_model = apps.get_model("lab", "Institution")
    duplicates = inst_model.objects.raw(RAW_SQL_QUERY)
    for duplicate in duplicates:
        similar_institutions = inst_model.objects.filter(
            name__iexact=duplicate.name, country__iexact=duplicate.country
        )
        kept_institution = similar_institutions[0]
        to_remove_institutions = similar_institutions[1:]
        # Updates participations to link to the institution we are going to keep,
        # and then delete the other institutions.
        to_remove_institutions_ids = to_remove_institutions.values_list("id", flat=True)
        apps.get_model("lab", "Participation").objects.filter(
            institution_id__in=to_remove_institutions_ids
        ).update(institution_id=kept_institution.id)
        inst_model.objects.filter(id__in=to_remove_institutions_ids).delete()


def convert_to_lowercase(_, __):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE lab_institution SET name = LOWER(name)")
        cursor.execute("UPDATE lab_institution SET country = LOWER(country)")


class Migration(migrations.Migration):
    dependencies = [
        ("lab", "0024_alter_project_name_alter_run_label"),
    ]
    operations = [
        migrations.RunSQL(
            "SET CONSTRAINTS ALL IMMEDIATE;", "SET CONSTRAINTS ALL DEFERRED;"
        ),
        migrations.RunPython(convert_to_lowercase, migrations.RunPython.noop),
        migrations.RunPython(merge_duplicate_institutions, migrations.RunPython.noop),
        migrations.RunSQL(
            "SET CONSTRAINTS ALL DEFERRED;", "SET CONSTRAINTS ALL IMMEDIATE;"
        ),
        migrations.AlterField(
            model_name="institution",
            name="country",
            field=shared.models.LowerCharField(
                blank=True, max_length=255, null=True, verbose_name="country"
            ),
        ),
        migrations.AlterField(
            model_name="institution",
            name="name",
            field=shared.models.LowerCharField(max_length=255, verbose_name="name"),
        ),
        migrations.AddConstraint(
            model_name="institution",
            constraint=models.UniqueConstraint(
                fields=("name", "country"), name="unique_name_country_per_institution"
            ),
        ),
    ]
