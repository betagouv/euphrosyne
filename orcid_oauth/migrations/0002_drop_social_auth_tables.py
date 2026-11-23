from django.db import migrations

# social_django was replaced by allauth.socialaccount, and 0001 copied its ORCID
# links to allauth. Its tables still hold the old links, OAuth tokens and
# partial sign-in pipeline data: drop them rather than leave them. Only
# social_auth_usersocialauth references another table (the user).
SOCIAL_AUTH_TABLES = [
    "social_auth_usersocialauth",
    "social_auth_association",
    "social_auth_code",
    "social_auth_nonce",
    "social_auth_partial",
]


class Migration(migrations.Migration):
    dependencies = [
        ("orcid_oauth", "0001_social_auth_to_allauth"),
    ]

    operations = [
        migrations.RunSQL(
            [f"DROP TABLE IF EXISTS {table}" for table in SOCIAL_AUTH_TABLES]
            + ["DELETE FROM django_migrations WHERE app = 'social_django'"],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
