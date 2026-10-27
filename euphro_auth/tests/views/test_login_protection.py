import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import aauthenticate, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.generators import SchemaGenerator

from euphro_auth.models import LoginAttempt, User

pytestmark = pytest.mark.django_db
PASSWORD = "test-pass-123"


@pytest.fixture(autouse=True)
def login_settings(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    settings.LOGIN_FAILURE_LIMIT = 5
    settings.LOGIN_LOCKOUT_SECONDS = 900


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
    with patch("euphro_auth.login_protection.timezone.now", return_value=now):
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

    attempt = LoginAttempt.objects.get()
    with (
        patch(
            "euphro_auth.login_protection.timezone.now",
            return_value=now + timedelta(seconds=60),
        ),
        patch("django.contrib.auth.backends.ModelBackend.authenticate") as verify,
    ):
        response = submit_login(client, route, password=PASSWORD)
        assert response.status_code == 429
        assert response["Retry-After"] == "840"
        verify.assert_not_called()
    attempt.refresh_from_db()
    assert attempt.failures == 5
    assert attempt.locked_until == now + timedelta(seconds=900)
    assert attempt.updated_at == now

    with patch(
        "euphro_auth.login_protection.timezone.now",
        return_value=now + timedelta(seconds=900),
    ):
        response = submit_login(client, route, password=PASSWORD)
    assert response.status_code == (302 if route == "web" else 200)
    attempt.refresh_from_db()
    assert attempt.failures == 0
    assert attempt.locked_until is None
    assert attempt.last_failure_at is None


def test_counter_is_shared_across_routes_case_and_ip(client, user):
    for route in ["web", "token_basic", "long_json", "long_basic"]:
        submit_login(client, route, email=user.email.upper(), REMOTE_ADDR="203.0.113.1")
    response = submit_login(client, "web", email=user.email, REMOTE_ADDR="203.0.113.2")
    assert response.status_code == 429
    assert submit_login(client, "token_basic", password=PASSWORD).status_code == 429
    attempt = LoginAttempt.objects.get()
    assert attempt.failures == 5
    assert len(attempt.identifier_hash) == 64
    assert user.email not in attempt.identifier_hash


@pytest.mark.parametrize("route", ["web", "token_basic", "long_json"])
def test_success_resets_counter_before_threshold(client, user, route):
    for _ in range(4):
        submit_login(client, "web", email=user.email)
    assert submit_login(client, route, password=PASSWORD).status_code in (200, 302)
    client.logout()
    assert submit_login(client, "web").status_code == 200
    assert LoginAttempt.objects.get().failures == 1


def test_failures_expire_after_inactivity(client, user):
    now = timezone.now()
    with patch("euphro_auth.login_protection.timezone.now", return_value=now):
        for _ in range(4):
            submit_login(client, "web", email=user.email)
    with patch(
        "euphro_auth.login_protection.timezone.now",
        return_value=now + timedelta(seconds=900),
    ):
        assert submit_login(client, "web").status_code == 200
    assert LoginAttempt.objects.get().failures == 1


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
    assert LoginAttempt.objects.get().failures == 5


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
    assert authenticate(**credentials) is None
    assert not LoginAttempt.objects.exists()


def test_async_authentication_uses_the_same_counter(user):
    async_authenticate = async_to_sync(aauthenticate)
    for _ in range(4):
        assert async_authenticate(email=user.email.upper(), password="wrong") is None
    assert authenticate(email=user.email, password="wrong") is None
    assert async_authenticate(email=user.email, password=PASSWORD) is None
    assert LoginAttempt.objects.get().failures == 5


@pytest.mark.django_db(transaction=True)
def test_concurrent_initial_attempts_stop_at_five_failures(user):
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
    assert sorted(statuses) == [200] * 4 + [429] * 4
    assert LoginAttempt.objects.get().failures == 5


def test_purge_removes_only_inactive_unlocked_counters():
    now = timezone.now()
    stale = now - timedelta(hours=25)
    expired = LoginAttempt.objects.create(
        identifier_hash="expired", locked_until=now - timedelta(hours=24)
    )
    successful = LoginAttempt.objects.create(identifier_hash="successful")
    active = LoginAttempt.objects.create(
        identifier_hash="active", locked_until=now + timedelta(hours=1)
    )
    recent = LoginAttempt.objects.create(identifier_hash="recent")
    LoginAttempt.objects.exclude(pk=recent.pk).update(updated_at=stale)
    call_command("purge_login_attempts", stdout=StringIO())
    assert set(LoginAttempt.objects.values_list("pk", flat=True)) == {
        active.pk,
        recent.pk,
    }
    assert not LoginAttempt.objects.filter(pk__in=[expired.pk, successful.pk]).exists()


def test_token_schema_documents_lockout_and_retry_header():
    schema = SchemaGenerator().get_schema(public=True)
    for path in ["/api/auth/token/", "/api/auth/long-token/"]:
        responses = schema["paths"][path]["post"]["responses"]
        assert "200" in responses
        assert responses["429"]["headers"]["Retry-After"]["schema"]["type"] == "integer"
        assert responses["429"]["content"]["application/json"]["schema"][
            "$ref"
        ].endswith("/LoginLockout")
