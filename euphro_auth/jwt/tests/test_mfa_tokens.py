import datetime
import logging
import re

import pytest
from django.test import Client
from django.urls import include, path, reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.tokens import RefreshToken

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from euphro_auth.tests.test_mfa import PASSWORD, enroll, sign_in

from ..tokens import EuphroRefreshToken

pytestmark = pytest.mark.django_db

PROJECTS_API_URL = "/api/token-probe/"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def token_probe(_request):
    return Response({"status": "ok"})


urlpatterns = [
    path("api/token-probe/", token_probe),
    path("", include("euphrosyne.urls")),
]


@pytest.fixture(autouse=True)
def mfa_required(settings):
    settings.ROOT_URLCONF = __name__
    settings.MFA_ADMIN_REQUIRED = True
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture(name="admin_user")
def admin_user_fixture():
    user = LabAdminUserFactory()
    user.set_password(PASSWORD)
    user.save()
    return user


@pytest.fixture(name="verified_client")
def verified_client_fixture(client, admin_user):
    sign_in(client, admin_user, enroll(admin_user))
    return client


def api_get(token, url=PROJECTS_API_URL):
    return Client().get(url, HTTP_AUTHORIZATION=f"Bearer {token}")


def refresh(token):
    return Client().post("/api/auth/token/refresh/", {"refresh": str(token)})


# Session tokens


def test_verified_admin_session_token_carries_admin_rights(verified_client):
    response = verified_client.post("/api/auth/token/")
    assert response.status_code == 200
    # Session clients get an access token only: no refresh token that would
    # outlive the session.
    assert set(response.json()) == {"access"}
    payload = token_backend.decode(response.json()["access"])
    assert payload["is_admin"] is True


def test_other_users_get_tokens_without_second_factor(client):
    user = StaffUserFactory()
    client.force_login(user)
    response = client.post("/api/auth/token/")
    assert response.status_code == 200
    access = response.json()["access"]
    assert token_backend.decode(access)["is_admin"] is False
    assert api_get(access).status_code == 200


def test_tokens_are_accepted_and_refreshed(admin_user):
    token = EuphroRefreshToken.for_user(admin_user)
    assert api_get(token.access_token).status_code == 200
    response = refresh(token)
    assert response.status_code == 200
    assert token_backend.decode(response.json()["access"])["is_admin"] is True


# Herma token page


def issued_token(response) -> str:
    content = response.content.decode()
    match = re.search(r'id="herma-token"[^>]*>([^<]+)</textarea>', content)
    assert match
    return match.group(1).strip()


def test_herma_page_issues_a_one_day_token(verified_client, admin_user, caplog):
    assert verified_client.get(reverse("admin:herma_token")).status_code == 200
    with caplog.at_level(logging.INFO, logger="euphro_auth.jwt.views"):
        response = verified_client.post(reverse("admin:herma_token"))
    token = RefreshToken(issued_token(response))
    assert token["is_admin"] is True
    lifetime = datetime.timedelta(seconds=token["exp"] - token["iat"])
    assert lifetime == datetime.timedelta(days=1)
    assert "Expire le" in response.content.decode()
    assert any(
        message.startswith(f"Herma token issued for user {admin_user.pk}")
        for message in caplog.messages
    )
    assert refresh(token).status_code == 200


def test_herma_page_needs_a_verified_session(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("admin:herma_token"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("mfa_activate_totp"))


def test_herma_page_is_reserved_to_administrators(client):
    client.force_login(StaffUserFactory())
    assert client.get(reverse("admin:herma_token")).status_code == 403
