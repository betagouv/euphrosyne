import base64
import datetime
import json
import time
from unittest.mock import patch

import pytest
from allauth.socialaccount.models import SocialAccount
from django.contrib import auth
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from euphro_auth.jwt.tokens import EuphroRefreshToken
from euphro_auth.models import User
from euphro_auth.password_lockout import LOCKOUT_MESSAGE
from orcid_oauth.tests.helpers import orcid_callback, start_orcid_login

pytestmark = pytest.mark.django_db
PASSWORD = "T8!vQ2#rM6@zL9$p"
CHANNELS = ["web", "basic", "jwt-json", "jwt-form", "long-basic"]


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


def password_request(client, channel, email, password, ip="192.0.2.1", **extra):
    extra["REMOTE_ADDR"] = ip
    if channel == "web":
        return client.post(
            reverse("account_login"), {"login": email, "password": password}, **extra
        )
    if channel in {"basic", "long-basic"}:
        credentials = base64.b64encode(f"{email}:{password}".encode()).decode()
        extra["HTTP_AUTHORIZATION"] = f"Basic {credentials}"
    url = "/api/auth/token/" if channel == "basic" else "/api/auth/long-token/"
    data = {"email": email, "password": password}
    if channel == "jwt-json":
        return client.post(
            url, json.dumps(data), content_type="application/json", **extra
        )
    return client.post(url, data, **extra)


def is_locked_out_response(channel, response) -> bool:
    if channel == "web":
        content = response.content.decode()
        return (
            response.status_code == 200
            and str(LOCKOUT_MESSAGE) in content
            and 'id="login-form"' not in content
        )
    return response.status_code == 429 and "ORCID" in response.json()["detail"]


def is_failure_response(channel, response) -> bool:
    if channel == "web":
        return (
            response.status_code == 200
            and 'id="login-form"' in response.content.decode()
        )
    return response.status_code == 401


def is_success_response(channel, response) -> bool:
    return response.status_code == (302 if channel == "web" else 200)


def fail(client, user, times, channel="jwt-json"):
    for _ in range(times):
        assert is_failure_response(
            channel, password_request(client, channel, user.email, "wrong-password")
        )


@pytest.mark.parametrize("channel", CHANNELS)
def test_fifth_password_failure_locks_every_channel(client, user, channel):
    fail(client, user, 4, channel)
    response = password_request(client, channel, user.email, "wrong-password")
    assert is_locked_out_response(channel, response)
    if channel == "web":
        assert reverse("orcid_login") in response.content.decode()
    for target in CHANNELS:
        with patch.object(
            User, "check_password", side_effect=AssertionError("blocked")
        ):
            response = password_request(
                client, target, user.email, PASSWORD, "192.0.2.99"
            )
        assert is_locked_out_response(target, response)
    assert not auth.get_user(client).is_authenticated


def test_shared_counter_normalizes_email_across_ips_and_user_agents(client, user):
    for index, channel in enumerate(CHANNELS):
        response = password_request(
            client,
            channel,
            user.email.upper() if index % 2 else user.email,
            "wrong-password",
            f"192.0.2.{index + 1}",
            HTTP_USER_AGENT=f"browser-{index}",
        )
        if index < 4:
            assert is_failure_response(channel, response)
    assert is_locked_out_response(channel, response)
    assert is_locked_out_response(
        "basic", password_request(client, "basic", user.email.upper(), PASSWORD)
    )


@pytest.mark.parametrize("channel", CHANNELS)
def test_successful_password_authentication_resets_shared_failures(
    client, user, channel
):
    fail(client, user, 4)
    response = password_request(client, channel, user.email.upper(), PASSWORD)
    assert is_success_response(channel, response)
    fail(Client(), user, 4)
    assert is_success_response(
        "jwt-json", password_request(Client(), "jwt-json", user.email, PASSWORD)
    )


def test_lockout_lasts_fifteen_minutes_from_the_fifth_failure(client, user, clock):
    for channel in CHANNELS:
        response = password_request(client, channel, user.email, "wrong-password")
        clock.advance(minutes=1)
    assert is_locked_out_response(channel, response)
    clock.advance(minutes=13, seconds=59)
    # Both correct and incorrect credentials must leave the deadline intact.
    assert is_locked_out_response(
        "basic", password_request(client, "basic", user.email, PASSWORD)
    )
    assert is_locked_out_response(
        "jwt-json", password_request(client, "jwt-json", user.email, "wrong-password")
    )
    clock.advance(seconds=2)
    assert is_success_response(
        "jwt-json", password_request(client, "jwt-json", user.email, PASSWORD)
    )


def test_failures_older_than_fifteen_minutes_are_not_counted(client, user, clock):
    fail(client, user, 4)
    clock.advance(minutes=15, seconds=1)
    fail(client, user, 4)
    assert is_success_response(
        "jwt-json", password_request(client, "jwt-json", user.email, PASSWORD)
    )


def test_lockout_does_not_affect_another_account_on_the_same_ip(client, user):
    for _ in range(5):
        password_request(client, "basic", user.email, "wrong-password")
    other = User.objects.create_user(
        email="other@example.com", password=PASSWORD, is_staff=True
    )
    assert is_success_response(
        "jwt-json", password_request(client, "jwt-json", other.email, PASSWORD)
    )
    assert is_locked_out_response(
        "jwt-json", password_request(client, "jwt-json", user.email, PASSWORD)
    )


def test_missing_credentials_and_bad_basic_headers_do_not_count(client, user):
    for _ in range(6):
        assert client.post("/api/auth/long-token/", {}).status_code == 400
        assert (
            client.post(
                "/api/auth/token/", HTTP_AUTHORIZATION="Basic invalid"
            ).status_code
            == 401
        )
    assert is_success_response(
        "jwt-json", password_request(client, "jwt-json", user.email, PASSWORD)
    )


def test_existing_session_and_refresh_remain_usable_during_lockout(client, user):
    refresh = EuphroRefreshToken.for_user(user)
    client.force_login(user)
    other_client = Client()
    for _ in range(5):
        password_request(other_client, "basic", user.email, "wrong-password")
    assert client.post("/api/auth/token/").status_code == 200
    assert (
        other_client.post(
            "/api/auth/token/refresh/", {"refresh": str(refresh)}
        ).status_code
        == 200
    )
    assert is_locked_out_response(
        "basic", password_request(Client(), "basic", user.email, PASSWORD)
    )


def test_orcid_still_authenticates_locked_account_without_resetting_password_limit(
    client, user
):
    for _ in range(5):
        password_request(client, "web", user.email, "wrong-password")
    uid = "0000-0002-1234-5678"
    SocialAccount.objects.create(user=user, provider="orcid", uid=uid)
    assert start_orcid_login(client).status_code == 302
    response = orcid_callback(client, uid)
    assert response.status_code == 302
    assert auth.get_user(client).pk == user.pk
    assert is_locked_out_response(
        "basic", password_request(Client(), "basic", user.email, PASSWORD)
    )
