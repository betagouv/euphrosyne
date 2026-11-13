"""Copy the ORCID links of social_django (``social_auth_usersocialauth``) to
allauth (``socialaccount_socialaccount``).

social_django is no longer installed, so its table is read with SQL. The table
is kept: it is dropped by a later migration, once this copy has been checked.
OAuth credentials kept by social_django are not copied: the platform never
uses them after sign-in.
"""

import json

from django.db import migrations

SOURCE_TABLE = "social_auth_usersocialauth"
OMITTED_EXTRA_DATA = {"access_token", "refresh_token"}


def copy_orcid_accounts(apps, schema_editor):
    connection = schema_editor.connection
    if SOURCE_TABLE not in connection.introspection.table_names():
        return
    social_account_model = apps.get_model("socialaccount", "SocialAccount")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, uid, extra_data, created, modified "
            f"FROM {SOURCE_TABLE} WHERE provider = %s",
            ["orcid"],
        )
        rows = cursor.fetchall()
    for user_id, uid, extra_data, created, modified in rows:
        if isinstance(extra_data, str):
            extra_data = json.loads(extra_data)
        account, _ = social_account_model.objects.get_or_create(
            provider="orcid",
            uid=uid,
            defaults={
                "user_id": user_id,
                "extra_data": {
                    key: value
                    for key, value in (extra_data or {}).items()
                    if key not in OMITTED_EXTRA_DATA
                },
            },
        )
        if account.user_id != user_id:
            raise RuntimeError(f"ORCID iD {uid} is already linked to another user.")
        social_account_model.objects.filter(pk=account.pk).update(
            date_joined=created, last_login=modified
        )


class Migration(migrations.Migration):
    dependencies = [
        ("euphro_auth", "0014_drop_axes_tables"),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]

    operations = [
        migrations.RunPython(copy_orcid_accounts, migrations.RunPython.noop),
    ]
