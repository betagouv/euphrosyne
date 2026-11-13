from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower


def check_case_insensitive_emails(apps, schema_editor):
    """allauth's account.0006 lowercases every user email, which must stay
    unique. Stop with an explicit message, before it fails on the unique
    constraint, when several accounts share an email up to letter case: which
    account to keep is a decision for an administrator."""
    user_model = apps.get_model("euphro_auth", "User")
    users = user_model.objects.using(schema_editor.connection.alias).annotate(
        email_lower=Lower("email")
    )
    duplicates = (
        users.values("email_lower")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .values_list("email_lower", flat=True)
    )
    if duplicates:
        user_ids = sorted(
            users.filter(email_lower__in=list(duplicates)).values_list(
                "id", flat=True
            )
        )
        raise RuntimeError(
            "Several accounts share an email address up to letter case "
            f"(user ids: {', '.join(map(str, user_ids))}). Merge or rename them, "
            "then run the migrations again."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("euphro_auth", "0014_drop_axes_tables"),
    ]
    run_before = [
        ("account", "0006_emailaddress_lower"),
    ]

    operations = [
        migrations.RunPython(check_case_insensitive_emails, migrations.RunPython.noop),
    ]
