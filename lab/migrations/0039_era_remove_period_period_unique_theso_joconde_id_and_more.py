# Generated by Django 5.0.6 on 2024-06-21 10:08

import django.db.models.deletion
from django.db import migrations, models


def move_period_to_era(apps, _):
    """We have to move period to era because we saved Opentheso Humanum 'era'
    with the field name 'period'."""
    period_model = apps.get_model("lab", "Period")
    era_model = apps.get_model("lab", "Era")
    objectgroup_model = apps.get_model("lab", "ObjectGroup")
    for period in period_model.objects.all():
        era = era_model.objects.create(
            label=period.label, concept_id=period.theso_joconde_id
        )
        for og in objectgroup_model.objects.filter(dating=period):
            og.dating_era = era
            og.save()
        period.delete()


def reverse_move_period_to_era(apps, _):
    period_model = apps.get_model("lab", "Period")
    era_model = apps.get_model("lab", "Era")
    objectgroup_model = apps.get_model("lab", "ObjectGroup")
    for era in era_model.objects.all():
        period = period_model.objects.create(
            label=era.label, theso_joconde_id=era.concept_id
        )
        for og in objectgroup_model.objects.filter(dating_era=era):
            og.dating = period
            og.save()
        era.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("lab", "0038_location_unique_geonames_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Era",
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
                    "concept_id",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Concept ID on Open Theso",
                    ),
                ),
                ("label", models.CharField(max_length=255, verbose_name="Label")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="era",
            constraint=models.UniqueConstraint(
                fields=("label", "concept_id"),
                name="era_thesorus_concept_unique_label_concept_id",
            ),
        ),
        migrations.AddConstraint(
            model_name="era",
            constraint=models.UniqueConstraint(
                fields=("concept_id",), name="era_thesorus_concept_unique_concept_id"
            ),
        ),
        migrations.AddField(
            model_name="objectgroup",
            name="dating_era",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="lab.era",
                verbose_name="Era",
            ),
        ),
        migrations.RunSQL(
            "SET CONSTRAINTS ALL IMMEDIATE;", "SET CONSTRAINTS ALL DEFERRED;"
        ),
        migrations.RunPython(
            move_period_to_era,
            reverse_move_period_to_era,
        ),
        migrations.RunSQL(
            "SET CONSTRAINTS ALL DEFERRED;", "SET CONSTRAINTS ALL IMMEDIATE;"
        ),
        migrations.RemoveConstraint(
            model_name="period",
            name="period_unique_theso_joconde_id",
        ),
        migrations.RemoveConstraint(
            model_name="period",
            name="period_unique_label_theso_joconde_id",
        ),
        migrations.RemoveField(
            model_name="objectgroup",
            name="dating",
        ),
        migrations.RemoveField(
            model_name="period",
            name="theso_joconde_id",
        ),
        migrations.AddField(
            model_name="objectgroup",
            name="dating_period",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="lab.period",
                verbose_name="Period",
            ),
        ),
        migrations.AddField(
            model_name="period",
            name="concept_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Concept ID on Open Theso",
            ),
        ),
        migrations.AlterField(
            model_name="period",
            name="label",
            field=models.CharField(max_length=255, verbose_name="Label"),
        ),
        migrations.AddConstraint(
            model_name="period",
            constraint=models.UniqueConstraint(
                fields=("label", "concept_id"),
                name="period_thesorus_concept_unique_label_concept_id",
            ),
        ),
        migrations.AddConstraint(
            model_name="period",
            constraint=models.UniqueConstraint(
                fields=("concept_id",), name="period_thesorus_concept_unique_concept_id"
            ),
        ),
    ]
