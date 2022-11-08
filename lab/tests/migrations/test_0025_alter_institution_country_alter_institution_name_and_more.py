import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from faker import Faker


def _reverse_before_tested_migration(app, executor: MigrationExecutor):
    app = apps.get_containing_app_config(__name__).name
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()

    migrate_from = [(app, "0024_alter_project_name_alter_run_label")]
    executor.migrate(migrate_from)
    return executor.loader.project_state(migrate_from).apps


def _migrate_to_latest(app, executor: MigrationExecutor):
    # Run the migration to test
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()

    migrate_to = [
        (app, "0025_alter_institution_country_alter_institution_name_and_more")
    ]
    executor.migrate(migrate_to)
    return executor.loader.project_state(migrate_to).apps


@pytest.mark.django_db
def test_merge_duplicate_institutions():
    app = apps.get_containing_app_config(__name__).name
    executor = MigrationExecutor(connection)

    old_apps = _reverse_before_tested_migration(app, executor)
    inst_model = old_apps.get_model("lab", "Institution")
    participation_model = old_apps.get_model("lab", "Participation")
    project_model = old_apps.get_model("lab", "Project")
    user_model = old_apps.get_model("euphro_auth", "User")
    insts = inst_model.objects.bulk_create(
        [
            inst_model(name="Louvre", country="France"),
            inst_model(name="Louvre", country="France"),
            inst_model(name="Louvre", country="France"),
            inst_model(name="MANN", country="Napoli"),
        ]
    )
    for index, institution in enumerate(insts):
        participation_model.objects.create(
            project=project_model.objects.create(name=f"Projet {index}"),
            institution=institution,
            user=user_model.objects.create(email=Faker().email()),
        )

    new_apps = _migrate_to_latest(app, executor)
    inst_model = new_apps.get_model("lab", "Institution")
    participation_model = new_apps.get_model("lab", "Participation")
    assert inst_model.objects.filter(name="louvre", country="france").count() == 1
    assert inst_model.objects.filter(name="mann", country="napoli").count() == 1

    louvre_inst = inst_model.objects.get(name="louvre", country="france")
    assert participation_model.objects.filter(institution=louvre_inst).count() == 3
