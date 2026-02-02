import re

from django.db import migrations


_SEPARATOR_RE = re.compile(r"([-\u2019'])")


def _capitalize_segment(segment: str) -> str:
    if not segment:
        return segment
    return segment[0].upper() + segment[1:].lower()


def _normalize_token(token: str) -> str:
    parts = _SEPARATOR_RE.split(token)
    normalized_parts = []
    for part in parts:
        if part == "":
            continue
        if _SEPARATOR_RE.fullmatch(part):
            normalized_parts.append(part)
        else:
            normalized_parts.append(_capitalize_segment(part))
    return "".join(normalized_parts)


def normalize_person_name(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return raw
    if not (raw.islower() or raw.isupper()):
        return raw
    tokens = raw.split()
    return " ".join(_normalize_token(token) for token in tokens)


def normalize_user_names(apps, schema_editor):
    User = apps.get_model("euphro_auth", "User")
    for user_id, first_name, last_name in User.objects.all().values_list(
        "id", "first_name", "last_name"
    ).iterator():
        new_first_name = normalize_person_name(first_name)
        new_last_name = normalize_person_name(last_name)
        if new_first_name != first_name or new_last_name != last_name:
            User.objects.filter(id=user_id).update(
                first_name=new_first_name,
                last_name=new_last_name,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("euphro_auth", "0012_user_preferred_language"),
    ]

    operations = [
        migrations.RunPython(normalize_user_names, migrations.RunPython.noop),
    ]
