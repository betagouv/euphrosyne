import importlib

import pytest
from django.apps import apps
from django.db import connection

from euphro_auth.models import User

pytestmark = pytest.mark.django_db

check_migration = importlib.import_module(
    "euphro_auth.migrations.0015_check_case_insensitive_emails"
)
lowercase_migration = importlib.import_module(
    "euphro_auth.migrations.0016_user_email_ci_unique"
)


@pytest.fixture(name="without_case_insensitive_constraint")
def without_case_insensitive_constraint_fixture():
    """Data as it was before migration 0016. The test transaction restores the
    constraint."""
    (constraint,) = User._meta.constraints
    with connection.schema_editor() as schema_editor:
        schema_editor.remove_constraint(User, constraint)


def create_raw_users(*emails: str) -> list[User]:
    # bulk_create skips User.save, which lowercases emails.
    return User.objects.bulk_create(User(email=email) for email in emails)


def run_migration_function(function):
    with connection.schema_editor() as schema_editor:
        function(apps, schema_editor)


@pytest.mark.usefixtures("without_case_insensitive_constraint")
def test_accounts_sharing_an_email_up_to_case_stop_the_migration():
    first, second, _ = create_raw_users(
        "Same.Person@example.com", "same.person@example.com", "other@example.com"
    )

    with pytest.raises(RuntimeError, match=f"user ids: {first.pk}, {second.pk}"):
        run_migration_function(check_migration.check_case_insensitive_emails)


@pytest.mark.usefixtures("without_case_insensitive_constraint")
def test_distinct_emails_pass():
    create_raw_users("Upper.Case@example.com", "other@example.com")

    run_migration_function(check_migration.check_case_insensitive_emails)


@pytest.mark.usefixtures("without_case_insensitive_constraint")
def test_existing_emails_are_lowercased():
    upper, lower = create_raw_users("Upper.Case@Example.COM", "lower@example.com")

    run_migration_function(lowercase_migration.lowercase_emails)

    upper.refresh_from_db()
    lower.refresh_from_db()
    assert upper.email == "upper.case@example.com"
    assert lower.email == "lower@example.com"
