from datetime import timedelta
from unittest.mock import patch

import pytest
from axes.models import AccessAttempt
from django.contrib import auth
from django.db.models import Sum
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from social_django.models import UserSocialAuth

from euphro_auth.jwt.tokens import EuphroRefreshToken
from euphro_auth.models import User
from orcid_oauth.backends import ORCIDOAuth2

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


@pytest.fixture(name="clock")
def mocked_clock():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mocked:
        with patch("axes.handlers.proxy.now", mocked):
            yield mocked


def password_request(client, email, password, ip="192.0.2.1", **extra):
    return client.post(
        reverse("admin:login"),
        {"username": email, "password": password},
        REMOTE_ADDR=ip,
        **extra,
    )


def failures(email):
    return (
        AccessAttempt.objects.filter(username=email).aggregate(
            count=Sum("failures_since_start")
        )["count"]
        or 0
    )


def test_fifth_password_failure_locks_web_login(client, user):
    for count in range(1, 6):
        response = password_request(client, user.email, "wrong-password")
        assert response.status_code == (429 if count == 5 else 200)
        assert failures(user.email) == count
    assert reverse("social:begin", args=("orcid",)) in response.content.decode()
    assert 'id="login-form"' not in response.content.decode()
    with patch.object(User, "check_password", side_effect=AssertionError("blocked")):
        response = password_request(client, user.email, PASSWORD, "192.0.2.99")
    assert response.status_code == 429
    assert failures(user.email) == 5
    assert not auth.get_user(client).is_authenticated


def test_shared_counter_normalizes_email_across_ips_and_user_agents(client, user):
    for index in range(5):
        response = password_request(
            client,
            user.email.upper() if index % 2 else user.email,
            "wrong-password",
            f"192.0.2.{index + 1}",
            HTTP_USER_AGENT=f"browser-{index}",
        )
        assert response.status_code == (429 if index == 4 else 200)
        assert failures(user.email) == index + 1
    assert set(AccessAttempt.objects.values_list("username", flat=True)) == {user.email}
    assert password_request(client, user.email.upper(), PASSWORD).status_code == 429


def test_successful_password_authentication_resets_shared_failures(client, user):
    for _ in range(4):
        password_request(client, user.email, "wrong-password")
    response = password_request(client, user.email.upper(), PASSWORD)
    assert response.status_code == 302
    assert failures(user.email) == 0


def test_lockout_expires_after_fifteen_minute_cooloff(client, user, clock):
    started = clock.return_value
    for index in range(5):
        clock.return_value = started + timedelta(minutes=index)
        response = password_request(client, user.email, "wrong-password")
    assert response.status_code == 429
    locked_at = clock.return_value
    clock.return_value = locked_at + timedelta(minutes=14, seconds=59)
    # Both correct and incorrect credentials must leave the original deadline intact.
    assert password_request(client, user.email, PASSWORD).status_code == 429
    assert password_request(client, user.email, "wrong-password").status_code == 429
    assert failures(user.email) == 5
    clock.return_value = locked_at + timedelta(minutes=15, seconds=1)
    assert password_request(client, user.email, PASSWORD).status_code == 302
    assert failures(user.email) == 0


def test_lockout_uses_axes_expiry_for_each_ip(client, user, clock):
    started = clock.return_value
    for index in range(5):
        clock.return_value = started + timedelta(minutes=index)
        response = password_request(
            client, user.email, "wrong-password", f"192.0.2.{index + 1}"
        )
    assert response.status_code == 429
    clock.return_value = started + timedelta(minutes=14, seconds=59)
    assert password_request(client, user.email, PASSWORD).status_code == 429
    # Axes expires the oldest IP's row after its own cooloff. The account then
    # has fewer than five unexpired failures and can authenticate again.
    clock.return_value = started + timedelta(minutes=15, seconds=1)
    assert password_request(Client(), user.email, PASSWORD).status_code == 302
    assert failures(user.email) == 0


def test_lockout_does_not_affect_another_account_on_the_same_ip(client, user):
    for _ in range(5):
        password_request(client, user.email, "wrong-password")
    other = User.objects.create_user(
        email="other@example.com",
        password=PASSWORD,
        is_staff=True,
        invitation_completed_at=timezone.now(),
    )
    assert password_request(client, other.email, PASSWORD).status_code == 302
    assert failures(user.email) == 5


def test_missing_credentials_do_not_count(client, user):
    for _ in range(6):
        assert client.post(reverse("admin:login"), {}).status_code == 200
    assert failures(user.email) == 0


def test_existing_session_and_refresh_remain_usable_during_lockout(client, user):
    refresh = EuphroRefreshToken.for_user(user)
    client.force_login(user)
    other_client = Client()
    for _ in range(5):
        password_request(other_client, user.email, "wrong-password")
    assert client.post("/api/auth/token/").status_code == 200
    assert (
        other_client.post(
            "/api/auth/token/refresh/", {"refresh": str(refresh)}
        ).status_code
        == 200
    )
    assert failures(user.email) == 5


def test_orcid_still_authenticates_locked_account_without_resetting_password_limit(
    client, user, settings
):
    settings.SOCIAL_AUTH_ORCID_KEY = "client-id"
    settings.SOCIAL_AUTH_ORCID_SECRET = "client-secret"
    for _ in range(5):
        password_request(client, user.email, "wrong-password")
    uid = "0000-0002-1234-5678"
    UserSocialAuth.objects.create(user=user, provider="orcid", uid=uid, id_key="orcid")
    begin = reverse("social:begin", args=("orcid",))
    assert client.post(begin).status_code == 302
    state = next(reversed(client.session["orcid_oauth2_transaction_index"]))
    with (
        patch.object(
            ORCIDOAuth2,
            "request_access_token",
            return_value={"orcid": uid, "access_token": "token"},
        ),
        patch.object(
            ORCIDOAuth2,
            "user_data",
            return_value={
                "orcid-identifier": {"path": uid},
                "person": {"name": {}, "emails": {"email": []}},
            },
        ),
    ):
        response = client.get(
            reverse("social:complete", args=("orcid",)),
            {"state": state, "code": "valid-code"},
        )
    assert response.status_code == 302
    assert auth.get_user(client).pk == user.pk
    assert failures(user.email) == 5
    assert password_request(Client(), user.email, PASSWORD).status_code == 429
