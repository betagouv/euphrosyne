from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.test import Client
from django.urls import include, path, reverse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from euphro_auth.jwt.tokens import EuphroRefreshToken

from .factories import StaffUserFactory

pytestmark = pytest.mark.django_db


@login_required
def protected_view(_request):
    return HttpResponse("ok")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_api_view(_request):
    return Response({"status": "ok"})


@login_required
def server_error_view(_request):
    return HttpResponse(status=500)


urlpatterns = [
    path("session-probe/", protected_view),
    path("api/session-probe/", protected_api_view),
    path("session-error/", server_error_view),
    path("", include("euphrosyne.urls")),
]


@pytest.fixture(autouse=True)
def session_urlconf(settings):
    settings.ROOT_URLCONF = __name__


@pytest.fixture(name="clock")
def mocked_clock():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mocked:
        yield mocked


@pytest.fixture(
    name="session_user",
    params=[(True, False, 900), (False, True, 900), (False, False, 3600)],
    ids=["lab-admin", "superuser", "ordinary-staff"],
)
def idle_session_user(request):
    is_lab_admin, is_superuser, timeout = request.param
    user = StaffUserFactory(is_lab_admin=is_lab_admin, is_superuser=is_superuser)
    return user, timeout


def test_password_login_sets_expiry_on_first_response(client, clock, session_user):
    user, timeout = session_user
    user.set_password("test-pass-123")
    user.save()

    response = client.post(
        reverse("admin:login"),
        {"username": user.email, "password": "test-pass-123"},
    )

    assert response.status_code == 302
    assert response.cookies[django_settings.SESSION_COOKIE_NAME]["max-age"] == timeout
    session = client.session
    assert session.get_expiry_age() == timeout
    assert Session.objects.get(session_key=session.session_key).expire_date == (
        clock.return_value + timedelta(seconds=timeout)
    )


@pytest.mark.parametrize("url", ["/session-probe/", "/api/session-probe/"])
def test_read_only_requests_keep_active_session_alive(client, clock, session_user, url):
    user, timeout = session_user
    client.force_login(user)
    started_at = clock.return_value

    for elapsed in [timeout - 1, 2 * (timeout - 1)]:
        clock.return_value = started_at + timedelta(seconds=elapsed)
        response = client.get(url)

        assert response.status_code == 200
        assert (
            response.cookies[django_settings.SESSION_COOKIE_NAME]["max-age"] == timeout
        )
        session = Session.objects.get(session_key=client.session.session_key)
        assert session.expire_date == clock.return_value + timedelta(seconds=timeout)


@pytest.mark.parametrize("overdue", [0, 1])
def test_expired_session_rejects_replayed_cookie(client, clock, session_user, overdue):
    user, timeout = session_user
    client.force_login(user)
    cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value
    clock.return_value += timedelta(seconds=timeout + overdue)

    # A fresh client deliberately resends the expired cookie to test the server,
    # independently of the browser's cookie expiration.
    replay_client = Client()
    replay_client.cookies[django_settings.SESSION_COOKIE_NAME] = cookie
    response = replay_client.get("/session-probe/")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login/?next=/session-probe/"
    assert not response.wsgi_request.user.is_authenticated
    assert "_auth_user_id" not in replay_client.session
    assert Session.objects.get(session_key=cookie).expire_date <= clock.return_value


def test_expired_session_cannot_access_api(client, clock, session_user):
    user, timeout = session_user
    client.force_login(user)
    clock.return_value += timedelta(seconds=timeout)

    response = client.get("/api/session-probe/")

    assert response.status_code == 403
    assert not response.wsgi_request.user.is_authenticated


def test_current_role_and_settings_determine_next_timeout(client, settings):
    settings.SESSION_IDLE_TIMEOUT_ADMIN = 30
    settings.SESSION_IDLE_TIMEOUT_USER = 120
    user = StaffUserFactory()
    client.force_login(user)
    assert client.session.get_expiry_age() == 120

    for is_lab_admin, is_superuser, timeout in [
        (True, False, 30),
        (False, True, 30),
        (False, False, 120),
    ]:
        user.is_lab_admin = is_lab_admin
        user.is_superuser = is_superuser
        user.save()

        assert client.get("/session-probe/").status_code == 200
        assert client.session.get_expiry_age() == timeout


def test_existing_session_adopts_policy_on_next_request(client, session_user):
    user, timeout = session_user
    client.force_login(user)
    session = client.session
    session.set_expiry(None)
    session.save()

    assert client.get("/session-probe/").status_code == 200
    assert client.session.get_expiry_age() == timeout


def test_logout_does_not_recreate_session(client, session_user):
    user, _timeout = session_user
    client.force_login(user)
    key = client.session.session_key

    response = client.post(f"{reverse('admin:logout')}?next=/login/")

    assert response.status_code == 302
    assert response.cookies[django_settings.SESSION_COOKIE_NAME]["max-age"] == 0
    assert not Session.objects.filter(session_key=key).exists()
    assert "_auth_user_id" not in client.session


def test_anonymous_request_does_not_set_session_expiry(client):
    response = client.get("/session-probe/")

    assert response.status_code == 302
    assert django_settings.SESSION_COOKIE_NAME not in response.cookies
    assert not Session.objects.exists()


def test_jwt_only_request_does_not_create_session(client, session_user):
    user, _timeout = session_user
    access = EuphroRefreshToken.for_user(user).access_token

    response = client.get("/api/session-probe/", HTTP_AUTHORIZATION=f"Bearer {access}")

    assert response.status_code == 200
    assert django_settings.SESSION_COOKIE_NAME not in response.cookies
    assert not Session.objects.exists()


def test_jwt_user_cannot_change_another_sessions_timeout(client, session_user):
    user, timeout = session_user
    client.force_login(user)
    token_user = StaffUserFactory(
        is_lab_admin=not (user.is_lab_admin or user.is_superuser)
    )
    access = EuphroRefreshToken.for_user(token_user).access_token

    # DRF authenticates this route with JWT before trying the session cookie.
    with patch.object(
        protected_api_view.cls, "authentication_classes", [JWTAuthentication]
    ):
        response = client.get(
            "/api/session-probe/", HTTP_AUTHORIZATION=f"Bearer {access}"
        )

    assert response.status_code == 200
    assert response.wsgi_request.user.pk == token_user.pk
    assert client.session.get_expiry_age() == timeout


def test_server_error_does_not_save_renewal(client, clock, session_user):
    user, timeout = session_user
    client.force_login(user)
    key = client.session.session_key
    expires_at = clock.return_value + timedelta(seconds=timeout)
    clock.return_value += timedelta(seconds=timeout - 1)

    response = client.get("/session-error/")

    assert response.status_code == 500
    assert django_settings.SESSION_COOKIE_NAME not in response.cookies
    assert Session.objects.get(session_key=key).expire_date == expires_at
    clock.return_value = expires_at
    assert client.get("/session-probe/").status_code == 302
