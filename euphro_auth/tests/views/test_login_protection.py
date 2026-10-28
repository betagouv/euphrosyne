import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from axes.models import AccessAttempt
from django.contrib.auth import aauthenticate, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import AsyncClient, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from euphro_auth.models import User

pytestmark = pytest.mark.django_db
PASSWORD = "test-pass-123"


@pytest.fixture(autouse=True)
def login_settings(settings, monkeypatch):
    # Resolve the function at call time so patches also freeze Axes' clock alias.
    # pylint: disable=unnecessary-lambda
    monkeypatch.setattr("axes.handlers.proxy.now", lambda: timezone.now())
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    settings.AXES_FAILURE_LIMIT = 5
    settings.AXES_COOLOFF_TIME = timedelta(seconds=900)


@pytest.fixture(name="user")
def login_user():
    return User.objects.create_user(
        email="login@example.com", password=PASSWORD, is_staff=True
    )


def submit_login(client, route, email="login@example.com", password="wrong", **extra):
    if route == "web":
        return client.post(
            reverse("admin:login"),
            {"username": email, "password": password},
            **extra,
        )
    url_name = (
        "token_obtain_pair_long" if route.startswith("long") else "token_obtain_pair"
    )
    data = {"email": email, "password": password}
    if route.endswith("basic"):
        credentials = base64.b64encode(f"{email}:{password}".encode()).decode()
        extra["HTTP_AUTHORIZATION"] = f"Basic {credentials}"
    return client.post(
        reverse(f"api:{url_name}"), data, content_type="application/json", **extra
    )


@pytest.mark.parametrize("route", ["web", "token_basic", "long_basic", "long_json"])
def test_fifth_failure_blocks_password_checks(client, user, route):
    now = timezone.now()
    with patch("euphro_auth.axes.timezone.now", return_value=now):
        for _ in range(4):
            response = submit_login(client, route, email=user.email)
            assert response.status_code == (200 if route == "web" else 401)
            assert "Retry-After" not in response
        response = submit_login(client, route)
        assert response.status_code == 429
        assert response["Retry-After"] == "900"
        assert "no-store" in response["Cache-Control"]
        if route == "web":
            assert reverse("admin_password_reset") in response.content.decode()
            assert reverse("social:begin", args=("orcid",)) in response.content.decode()
        else:
            assert set(response.json()) == {"detail"}

    attempt = AccessAttempt.objects.get()
    with (
        patch(
            "euphro_auth.axes.timezone.now",
            return_value=now + timedelta(seconds=60),
        ),
        patch("django.contrib.auth.backends.ModelBackend.authenticate") as verify,
    ):
        response = submit_login(client, route, password=PASSWORD)
        assert response.status_code == 429
        assert response["Retry-After"] == "840"
        verify.assert_not_called()
    attempt.refresh_from_db()
    assert attempt.failures_since_start == 5
    assert attempt.attempt_time == now

    with patch(
        "euphro_auth.axes.timezone.now",
        return_value=now + timedelta(seconds=901),
    ):
        response = submit_login(client, route, password=PASSWORD)
    assert response.status_code == (302 if route == "web" else 200)
    assert not AccessAttempt.objects.exists()


def test_counter_is_shared_across_routes_case_and_ip(client, user):
    for route in ["web", "token_basic", "long_json", "long_basic"]:
        submit_login(client, route, email=user.email.upper(), REMOTE_ADDR="203.0.113.1")
    response = submit_login(client, "web", email=user.email, REMOTE_ADDR="203.0.113.2")
    assert response.status_code == 429
    assert submit_login(client, "token_basic", password=PASSWORD).status_code == 429
    attempt = AccessAttempt.objects.get()
    assert attempt.failures_since_start == 5
    assert len(attempt.username) == 64
    assert user.email not in attempt.username
    assert attempt.ip_address == "0.0.0.0"
    assert user.email not in attempt.post_data
    assert user.email.upper() not in attempt.post_data
    assert "wrong" not in attempt.post_data


def test_user_agent_changes_do_not_reset_failures(client, user):
    for index in range(5):
        response = submit_login(
            client, "web", email=user.email, HTTP_USER_AGENT=f"client/{index}"
        )
    assert response.status_code == 429
    assert (
        sum(AccessAttempt.objects.values_list("failures_since_start", flat=True)) == 5
    )
    assert (
        submit_login(
            client, "web", password=PASSWORD, HTTP_USER_AGENT="another-client"
        ).status_code
        == 429
    )


@pytest.mark.parametrize("route", ["web", "token_basic", "long_json"])
def test_success_resets_counter_before_threshold(client, user, route):
    for _ in range(4):
        submit_login(client, "web", email=user.email)
    assert submit_login(client, route, password=PASSWORD).status_code in (200, 302)
    client.logout()
    assert submit_login(client, "web").status_code == 200
    assert AccessAttempt.objects.get().failures_since_start == 1


def test_failures_expire_after_inactivity(client, user):
    now = timezone.now()
    with patch("euphro_auth.axes.timezone.now", return_value=now):
        for _ in range(4):
            submit_login(client, "web", email=user.email)
    with patch(
        "euphro_auth.axes.timezone.now",
        return_value=now + timedelta(seconds=901),
    ):
        assert submit_login(client, "web").status_code == 200
    assert AccessAttempt.objects.get().failures_since_start == 1


@pytest.mark.parametrize("account_state", ["missing", "inactive"])
def test_unknown_and_inactive_accounts_are_also_limited(client, account_state):
    if account_state == "inactive":
        User.objects.create_user(
            email="login@example.com", password=PASSWORD, is_active=False
        )
    for _ in range(4):
        assert submit_login(client, "web", password=PASSWORD).status_code == 200
    response = submit_login(client, "web", password=PASSWORD)
    assert response.status_code == 429
    assert b"login@example.com" not in response.content


def test_other_accounts_and_existing_sessions_remain_usable(client, user):
    for _ in range(5):
        submit_login(client, "web")
    other = User.objects.create_user(
        email="other@example.com", password=PASSWORD, is_staff=True
    )
    assert (
        submit_login(
            client, "token_basic", email=other.email, password=PASSWORD
        ).status_code
        == 200
    )
    client.force_login(user)
    response = client.post(reverse("api:token_obtain_pair"))
    assert response.status_code == 200
    assert int(client.session["_auth_user_id"]) == user.pk
    refresh = response.json()["refresh"]
    response = client.post(reverse("api:token_refresh"), {"refresh": refresh})
    assert response.status_code == 200


def test_orcid_and_recovery_are_available_during_lockout(client, user, settings):
    for _ in range(5):
        submit_login(client, "web")
    assert client.get(reverse("admin:login")).status_code == 200
    assert client.get(reverse("admin_password_reset")).status_code == 200
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert (
        client.post(reverse("admin_password_reset"), {"email": user.email}).status_code
        == 302
    )
    settings.SOCIAL_AUTH_ORCID_KEY = "client-id"
    settings.SOCIAL_AUTH_ORCID_SECRET = "client-secret"
    response = client.post(reverse("social:begin", args=("orcid",)))
    assert response.status_code == 302
    assert response.url.startswith("https://orcid.org/oauth/authorize?")
    invitation_url = reverse(
        "registration_token",
        args=(
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ),
    )
    assert client.get(invitation_url, follow=True).status_code == 200
    assert AccessAttempt.objects.get().failures_since_start == 5


@pytest.mark.parametrize(
    "credentials",
    [
        {},
        {"email": ""},
        {"email": "   ", "password": "bad"},
        {"email": "login@example.com"},
    ],
)
def test_missing_credentials_do_not_create_counters(credentials):
    assert authenticate(request=RequestFactory().post("/login/"), **credentials) is None
    assert not AccessAttempt.objects.exists()


def test_async_authentication_uses_the_same_counter(user):
    async_authenticate = async_to_sync(aauthenticate)
    for _ in range(4):
        assert (
            async_authenticate(
                request=RequestFactory().post("/login/"),
                email=user.email.upper(),
                password="wrong",
            )
            is None
        )
    assert (
        authenticate(
            request=RequestFactory().post("/login/"), email=user.email, password="wrong"
        )
        is None
    )
    assert (
        async_authenticate(
            request=RequestFactory().post("/login/"),
            email=user.email,
            password=PASSWORD,
        )
        is None
    )
    assert AccessAttempt.objects.get().failures_since_start == 5


def test_async_api_uses_json_lockout_response(user):
    post = async_to_sync(AsyncClient().post)
    for _ in range(5):
        response = post(
            reverse("api:token_obtain_pair_long"),
            {"email": user.email, "password": "wrong"},
            content_type="application/json",
        )
    assert response.status_code == 429
    assert set(response.json()) == {"detail"}
    assert 0 < int(response["Retry-After"]) <= 900
    assert "no-store" in response["Cache-Control"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_failures_trigger_account_lockout(user):
    if connection.vendor != "postgresql":
        pytest.skip("Row locking is tested against PostgreSQL")
    barrier = Barrier(8)

    def attempt_login(_):
        close_old_connections()
        try:
            barrier.wait(timeout=15)
            return submit_login(Client(), "web", email=user.email).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(attempt_login, range(8)))
    assert set(statuses) <= {200, 429}
    assert 5 <= AccessAttempt.objects.get().failures_since_start <= 8
    assert submit_login(Client(), "web", password=PASSWORD).status_code == 429


def test_axes_reset_command_unlocks_only_the_selected_account(client, user):
    for _ in range(5):
        submit_login(client, "web", email=user.email)
        submit_login(client, "web", email="other@example.com")
    attempt = AccessAttempt.objects.earliest("pk")
    call_command("axes_reset_username", attempt.username, stdout=StringIO())
    assert (
        submit_login(client, "web", email=user.email, password=PASSWORD).status_code
        == 302
    )
    assert submit_login(client, "web", email="other@example.com").status_code == 429
