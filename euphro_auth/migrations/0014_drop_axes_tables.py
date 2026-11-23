from django.db import migrations

# django-axes was replaced by allauth rate limits. Its tables held login attempts
# (email addresses, IP addresses, user agents): drop them rather than leave them.
# Referencing tables first.
AXES_TABLES = [
    "axes_accessattemptexpiration",
    "axes_accessattempt",
    "axes_accessfailurelog",
    "axes_accesslog",
]


class Migration(migrations.Migration):
    dependencies = [
        ("euphro_auth", "0013_normalize_user_names"),
    ]

    operations = [
        migrations.RunSQL(
            [f"DROP TABLE IF EXISTS {table}" for table in AXES_TABLES]
            + ["DELETE FROM django_migrations WHERE app = 'axes'"],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
