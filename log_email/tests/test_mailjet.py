from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from log_email.providers.mailjet import MAILJET_BASE, MailjetProvider


@override_settings(
    MAILERS={
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": "in-v3.mailjet.com",
                "username": "api-key",
                "password": "secret-key",
            },
        }
    }
)
def test_list_messages_uses_mailjet_credentials():
    response = mock.Mock()
    response.json.return_value = {"Data": []}

    with mock.patch(
        "log_email.providers.mailjet.requests.get", return_value=response
    ) as get:
        assert MailjetProvider().list_messages(limit=25) == []

    get.assert_called_once_with(
        f"{MAILJET_BASE}/message?ShowContactAlt=true&ShowSubject=true",
        auth=("api-key", "secret-key"),
        params={"Limit": 25, "Sort": "ArrivedAt DESC"},
        timeout=5,
    )
    response.raise_for_status.assert_called_once_with()


@override_settings(
    MAILERS={
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {"host": "localhost"},
        }
    }
)
def test_list_messages_requires_a_mailjet_configuration():
    with pytest.raises(ImproperlyConfigured, match="No Mailjet configuration"):
        MailjetProvider().list_messages()


@override_settings(
    MAILERS={
        "default": {
            "OPTIONS": {
                "host": "in-v3.mailjet.com",
                "username": "api-key",
            }
        }
    }
)
def test_list_messages_requires_mailjet_credentials():
    with pytest.raises(ImproperlyConfigured, match="'password'"):
        MailjetProvider().list_messages()


@override_settings(
    MAILERS={
        "default": {
            "OPTIONS": {
                "host": "in-v3.mailjet.com",
                "username": "api-key",
                "password": "secret-key",
            }
        },
        "secondary": {
            "OPTIONS": {
                "host": "smtp.mailjet.com",
                "username": "other-api-key",
                "password": "other-secret-key",
            }
        },
    }
)
def test_list_messages_rejects_multiple_mailjet_configurations():
    with pytest.raises(ImproperlyConfigured, match="Multiple Mailjet configurations"):
        MailjetProvider().list_messages()
