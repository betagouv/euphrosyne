import importlib
import json

import pytest
from allauth.socialaccount.models import SocialAccount
from django.apps import apps
from django.contrib import auth
from django.db import connection
from django.utils import timezone

from euphro_auth.models import User

from .helpers import orcid_callback, start_orcid_login

pytestmark = pytest.mark.django_db

migration = importlib.import_module(
    "orcid_oauth.migrations.0001_social_auth_to_allauth"
)


@pytest.fixture(name="social_auth_table")
def social_auth_table_fixture():
    """The table social_django leaves behind once uninstalled."""
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE social_auth_usersocialauth ("
            "id serial PRIMARY KEY, provider varchar(32) NOT NULL, "
            "uid varchar(255) NOT NULL, user_id bigint NOT NULL, "
            "created timestamp with time zone NOT NULL, "
            "modified timestamp with time zone NOT NULL, "
            "extra_data jsonb NOT NULL, id_key varchar(255) NOT NULL)"
        )
    yield
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS social_auth_usersocialauth")


def insert_social_auth(user, provider, uid, extra_data, created):
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO social_auth_usersocialauth "
            "(provider, uid, user_id, created, modified, extra_data, id_key) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [provider, uid, user.pk, created, created, json.dumps(extra_data), "id"],
        )


def run_migration():
    with connection.schema_editor() as schema_editor:
        migration.copy_orcid_accounts(apps, schema_editor)


@pytest.mark.usefixtures("social_auth_table")
def test_orcid_links_are_copied_and_still_sign_in(client):
    user = User.objects.create_user(
        email="orcid@example.com",
        password=None,
        invitation_completed_at=timezone.now(),
    )
    other = User.objects.create_user(email="other@example.com", password=None)
    uid = "0000-0002-1234-5678"
    created = timezone.now() - timezone.timedelta(days=400)
    insert_social_auth(
        user,
        "orcid",
        uid,
        {
            "id": uid,
            "auth_time": 1700000000,
            "expires": 631138518,
            "token_type": "bearer",
            "access_token": "secret-access-token",
            "refresh_token": "secret-refresh-token",
        },
        created,
    )
    insert_social_auth(other, "other-provider", "other-uid", {}, created)

    run_migration()
    run_migration()  # Idempotent.

    account = SocialAccount.objects.get()
    assert (account.provider, account.uid, account.user_id) == ("orcid", uid, user.pk)
    assert account.extra_data == {
        "id": uid,
        "auth_time": 1700000000,
        "expires": 631138518,
        "token_type": "bearer",
    }
    assert account.date_joined == created

    start_orcid_login(client)
    orcid_callback(client, uid)
    assert auth.get_user(client).pk == user.pk


@pytest.mark.usefixtures("social_auth_table")
def test_conflicting_link_stops_the_migration():
    user = User.objects.create_user(email="orcid@example.com", password=None)
    other = User.objects.create_user(email="other@example.com", password=None)
    uid = "0000-0002-1234-5678"
    SocialAccount.objects.create(user=other, provider="orcid", uid=uid)
    insert_social_auth(user, "orcid", uid, {}, timezone.now())

    with pytest.raises(RuntimeError):
        run_migration()


def test_missing_social_auth_table_is_a_no_op():
    run_migration()
    assert not SocialAccount.objects.exists()


drop_migration = importlib.import_module(
    "orcid_oauth.migrations.0002_drop_social_auth_tables"
)


def run_drop_migration():
    with connection.cursor() as cursor:
        for statement in drop_migration.Migration.operations[0].sql:
            cursor.execute(statement)


@pytest.mark.usefixtures("social_auth_table")
def test_social_auth_tables_and_migration_history_are_dropped():
    with connection.cursor() as cursor:
        for table in drop_migration.SOCIAL_AUTH_TABLES[1:]:
            cursor.execute(f"CREATE TABLE {table} (id serial PRIMARY KEY)")
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) "
            "VALUES ('social_django', '0001_initial', now())"
        )

    run_drop_migration()
    run_drop_migration()  # Tables already dropped.

    assert not set(drop_migration.SOCIAL_AUTH_TABLES) & set(
        connection.introspection.table_names()
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM django_migrations WHERE app = 'social_django'")
        assert cursor.fetchone() is None
