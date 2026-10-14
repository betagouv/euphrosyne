from datetime import datetime, timezone
from unittest import mock

import pytest
from django.contrib import admin
from django.test import RequestFactory, override_settings
from django.urls import reverse

from euphro_auth.tests.factories import StaffUserFactory
from log_email.admin import EmailLogAdmin
from log_email.models import EmailLog


@pytest.mark.parametrize(
    "message_count, page, expected_ids",
    [
        (0, 1, []),
        (2, 1, ["0", "1"]),
        (101, 1, [str(i) for i in range(100)]),
        (101, 2, ["100"]),
    ],
)
@override_settings(
    NAV_GET_NAV_ITEMS=lambda _request: [],
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
def test_email_log_changelist_renders(message_count, page, expected_ids):
    request = RequestFactory().get(
        reverse("admin:log_email_emaillog_changelist"), {"p": page}
    )
    request.user = StaffUserFactory.build(id=1, is_superuser=True, is_lab_admin=True)
    model_admin = EmailLogAdmin(EmailLog, admin.site)
    messages = [
        {
            "id": str(i),
            "to": "recipient@example.com",
            "subject": f"Test email {i}",
            "status": "sent",
            "date": datetime(2026, 10, 14, tzinfo=timezone.utc),
        }
        for i in range(message_count)
    ]

    with mock.patch("log_email.admin.get_email_provider") as get_provider:
        get_provider.return_value.list_messages.return_value = messages
        response = model_admin.changelist_view(request)
        response.render()

    assert response.status_code == 200
    get_provider.return_value.list_messages.assert_called_once_with(limit=200)
    changelist = response.context_data["cl"]
    assert changelist.result_count == message_count
    assert [message.id for message in changelist.result_list] == expected_ids
    for message_id in expected_ids:
        assert f"Test email {message_id}" in response.content.decode()
