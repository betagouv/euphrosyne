from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string
from django.utils.html import escape

PAYLOAD = '<img src=x onerror="alert(1)"> & "quoted"'


@pytest.mark.parametrize(
    ("template", "field"),
    [
        ("invitation_email.html", "site_url"),
        ("project_invitation_email.html", "project_name"),
        ("data_request/email/data-request-created.html", "facility_name"),
        ("data_request/email/data-links.html", "facility_name"),
        ("radiation_protection/email/employer_information_reminder.html", "user"),
        (
            "radiation_protection/email/employer_information_reminder_summary.html",
            "participations",
        ),
        ("radiation_protection/email/radioprotection_invitation.html", "user"),
    ],
)
def test_html_emails_escape_untrusted_values(template, field):
    user = SimpleNamespace(
        first_name=PAYLOAD,
        last_name=PAYLOAD,
        email=PAYLOAD,
        get_full_name=lambda: PAYLOAD,
    )
    context = {
        "site_url": "https://example.com/",
        "uid": "uid",
        "token": "token",
        "project_id": 1,
        "user": user,
        "invitation_type": "RETRY",
        "run": SimpleNamespace(label=PAYLOAD),
        "project": SimpleNamespace(name=PAYLOAD),
        "participations": [SimpleNamespace(user=user, project_id=1)],
    }
    if field not in {"user", "participations"}:
        context[field] = PAYLOAD

    html = render_to_string(template, context)

    assert PAYLOAD not in html
    assert str(escape(PAYLOAD)) in html
