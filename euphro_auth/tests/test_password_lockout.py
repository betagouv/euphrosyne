import datetime
import logging
import time
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib import auth
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from euphro_auth.adapters import LOCKOUT_MESSAGE
from euphro_auth.models import User
from euphro_auth.tests.test_accounts import NEW_PASSWORD, request_reset, reset_link
from orcid_oauth.tests.helpers import orcid_callback, start_orcid_login

pytestmark = pytest.mark.django_db
PASSWORD = "T8!vQ2#rM6@zL9$p"


@pytest.fixture(autouse=True)
def local_static_storage(settings):
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture(name="user")
def password_user():
    return User.objects.create_user(
        email="locked@example.com",
        password=PASSWORD,
        is_staff=True,
        invitation_completed_at=timezone.now(),
    )


class Clock:
    def __init__(self):
        self.now = time.time()

    def advance(self, **kwargs):
        self.now += datetime.timedelta(**kwargs).total_seconds()


@pytest.fixture(name="clock")
def mocked_clock():
    """Rate limits and the database cache read time.time()."""
    clock = Clock()
    with (
        patch("time.time", side_effect=lambda: clock.now),
        patch(
            "django.utils.timezone.now",
            side_effect=lambda: datetime.datetime.fromtimestamp(
                clock.now, tz=datetime.UTC
            ),
        ),
    ):
        yield clock


def password_request(client, email, password, ip="192.0.2.1", **extra):
    return client.post(
        reverse("account_login"),
        {"login": email, "password": password},
        REMOTE_ADDR=ip,
        **extra,
    )


def is_locked_out_response(response) -> bool:
    content = response.content.decode()
    return (
        response.status_code == 200
        and str(LOCKOUT_MESSAGE) in content
        and 'id="login-form"' not in content
        and reverse("orcid_login") in content
    )


def is_failure_response(response) -> bool:
    return (
        response.status_code == 200 and 'id="login-form"' in response.content.decode()
    )


def is_success_response(response) -> bool:
    return response.status_code == 302


def fail(client, user, times):
    for _ in range(times):
        assert is_failure_response(password_request(client, user.email, "wrong"))


def test_five_password_failures_lock_password_sign_in(client, user):
    fail(client, user, 5)
    with patch.object(User, "check_password", side_effect=AssertionError("blocked")):
        response = password_request(Client(), user.email, PASSWORD, "192.0.2.99")
    assert is_locked_out_response(response)
    assert not auth.get_user(client).is_authenticated


def test_shared_counter_normalizes_email_across_ips_and_user_agents(client, user):
    for index in range(5):
        assert is_failure_response(
            password_request(
                Client(),
                user.email.upper() if index % 2 else user.email,
                "wrong",
                f"192.0.2.{index + 1}",
                HTTP_USER_AGENT=f"browser-{index}",
            )
        )
    assert is_locked_out_response(
        password_request(client, user.email.upper(), PASSWORD)
    )


def test_lockout_lifts_when_the_oldest_failure_is_fifteen_minutes_old(
    client, user, clock
):
    for _ in range(5):
        password_request(client, user.email, "wrong")
        clock.advance(minutes=1)
    clock.advance(minutes=9, seconds=59)
    assert is_locked_out_response(password_request(client, user.email, PASSWORD))
    clock.advance(seconds=2)
    assert is_success_response(password_request(client, user.email, PASSWORD))


def test_password_reset_lifts_the_lockout(client, user):
    fail(client, user, 5)
    request_reset(client, user.email)
    response = client.get(reset_link(), follow=True)
    client.post(
        response.redirect_chain[-1][0],
        {"password1": NEW_PASSWORD, "password2": NEW_PASSWORD},
    )
    assert is_success_response(password_request(Client(), user.email, NEW_PASSWORD))


def test_failures_older_than_fifteen_minutes_are_not_counted(client, user, clock):
    fail(client, user, 4)
    clock.advance(minutes=15, seconds=1)
    fail(client, user, 4)
    assert is_success_response(password_request(client, user.email, PASSWORD))


def test_lockout_does_not_affect_another_account_on_the_same_ip(client, user):
    fail(client, user, 5)
    other = User.objects.create_user(
        email="other@example.com", password=PASSWORD, is_staff=True
    )
    assert is_success_response(password_request(Client(), other.email, PASSWORD))
    assert is_locked_out_response(password_request(Client(), user.email, PASSWORD))


def test_existing_session_remains_usable_during_lockout(client, user):
    client.force_login(user)
    fail(Client(), user, 5)
    assert client.post("/api/auth/token/").status_code == 200
    assert is_locked_out_response(password_request(Client(), user.email, PASSWORD))


def test_orcid_still_authenticates_locked_account_without_resetting_password_limit(
    client, user
):
    fail(client, user, 5)
    uid = "0000-0002-1234-5678"
    SocialAccount.objects.create(user=user, provider="orcid", uid=uid)
    assert start_orcid_login(client).status_code == 302
    response = orcid_callback(client, uid)
    assert response.status_code == 302
    assert auth.get_user(client).pk == user.pk
    assert is_locked_out_response(password_request(Client(), user.email, PASSWORD))


# Journal


def test_wrong_password_logs_the_account_not_the_email_or_password(
    client, user, caplog
):
    with caplog.at_level(logging.WARNING, logger="euphro_auth"):
        password_request(client, user.email.upper(), "wrong-password")
    assert [(r.levelno, r.getMessage()) for r in caplog.records] == [
        (logging.WARNING, f"Password sign-in failed for user {user.pk}")
    ]
    assert "locked" not in caplog.text
    assert "wrong-password" not in caplog.text


def test_wrong_password_for_unknown_address_logs_a_neutral_mention(client, caplog):
    with caplog.at_level(logging.WARNING, logger="euphro_auth"):
        password_request(client, "nobody@example.com", "wrong-password")
    assert caplog.messages == ["Password sign-in failed for unknown account"]
    assert "nobody" not in caplog.text


def test_successful_password_sign_in_logs_nothing(client, user, caplog):
    with caplog.at_level(logging.DEBUG, logger="euphro_auth"):
        assert is_success_response(password_request(client, user.email, PASSWORD))
    assert caplog.messages == []


def test_lockout_refusal_is_logged_with_its_code(client, user, caplog):
    fail(client, user, 5)
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="euphro_auth"):
        response = password_request(Client(), user.email, PASSWORD, "192.0.2.99")
    assert is_locked_out_response(response)
    assert caplog.messages == [
        f"Password sign-in refused for user {user.pk} (too_many_login_attempts)"
    ]
