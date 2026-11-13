import importlib

import pytest
from django.apps import apps
from django.db import connection

from euphro_auth.models import User

pytestmark = pytest.mark.django_db

migration = importlib.import_module(
    "euphro_auth.migrations.0015_check_case_insensitive_emails"
)


def run_check():
    with connection.schema_editor() as schema_editor:
        migration.check_case_insensitive_emails(apps, schema_editor)


def test_accounts_sharing_an_email_up_to_case_stop_the_migration():
    first = User.objects.create(email="Same.Person@example.com")
    second = User.objects.create(email="same.person@example.com")
    User.objects.create(email="other@example.com")

    with pytest.raises(RuntimeError, match=f"user ids: {first.pk}, {second.pk}"):
        run_check()


def test_distinct_emails_pass():
    User.objects.create(email="Upper.Case@example.com")
    User.objects.create(email="other@example.com")

    run_check()
