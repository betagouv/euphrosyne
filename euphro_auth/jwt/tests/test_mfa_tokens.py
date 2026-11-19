import logging
import re

import pytest
from django.test import Client
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from ...tests.factories import LabAdminUserFactory, StaffUserFactory
from ..tokens import EuphroRefreshToken

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def mfa_required(settings):
    settings.MFA_ADMIN_REQUIRED = True
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


def verified_login(client, user):
    device = TOTPDevice.objects.create(user=user, name="Authenticator")
    client.force_login(user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()


# --- /api/auth/token/ ------------------------------------------------------------


def test_session_token_from_verified_session_has_mfa_claim(client):
    user = LabAdminUserFactory()
    verified_login(client, user)
    response = client.post("/api/auth/token/")
    assert response.status_code == 200
    assert RefreshToken(response.json()["refresh"])["mfa"] is True
    assert AccessToken(response.json()["access"])["mfa"] is True


def test_session_token_from_unverified_session_has_no_mfa_claim(client, settings):
    settings.MFA_ADMIN_REQUIRED = False
    client.force_login(LabAdminUserFactory())
    response = client.post("/api/auth/token/")
    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["mfa"] is False


def test_session_token_for_non_admin_has_no_mfa_claim(client):
    client.force_login(StaffUserFactory())
    response = client.post("/api/auth/token/")
    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["mfa"] is False


# --- Herma token page ------------------------------------------------------------


def test_herma_token_page_requires_verified_session(client):
    user = LabAdminUserFactory()
    TOTPDevice.objects.create(user=user, name="Authenticator")
    client.force_login(user)
    response = client.get(reverse("admin:herma_token"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("mfa_verify"))
    response = client.post(reverse("admin:herma_token"))
    assert response.status_code == 302


def test_herma_token_page_forbidden_for_non_admin(client):
    client.force_login(StaffUserFactory())
    assert client.get(reverse("admin:herma_token")).status_code == 403


def test_herma_token_page_without_mfa_when_mfa_disabled(client, settings):
    settings.MFA_ADMIN_REQUIRED = False
    client.force_login(LabAdminUserFactory())
    response = client.post(reverse("admin:herma_token"))
    assert response.status_code == 200
    match = re.search(
        r'<textarea[^>]*id="herma-token"[^>]*>([^<]+)</textarea>',
        response.content.decode(),
    )
    assert match
    assert EuphroRefreshToken(match.group(1).strip())["mfa"] is False


def test_herma_token_page_issues_refreshable_token(client, caplog):
    user = LabAdminUserFactory()
    verified_login(client, user)
    response = client.get(reverse("admin:herma_token"))
    assert response.status_code == 200
    assert 'id="herma-token"' not in response.content.decode()

    with caplog.at_level(logging.INFO, logger="euphro_auth.jwt.views"):
        response = client.post(reverse("admin:herma_token"))
    assert response.status_code == 200
    match = re.search(
        r'<textarea[^>]*id="herma-token"[^>]*>([^<]+)</textarea>',
        response.content.decode(),
    )
    assert match
    raw_token = match.group(1).strip()
    assert raw_token not in caplog.text
    assert "Herma token issued" in caplog.text

    refresh = EuphroRefreshToken(raw_token)
    assert refresh["mfa"] is True
    assert refresh["user_id"] == user.pk
    assert refresh["is_admin"] is True

    # Herma stores it as its refresh token and calls the standard refresh view.
    response = Client().post(
        "/api/auth/token/refresh/",
        {"refresh": raw_token},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["mfa"] is True


# --- JWT authentication and refresh with the mfa claim -----------------------


# IsAuthenticated API view authenticated with the default (JWT) classes.
PROBE_URL = "/api/mfa-jwt-probe/"


@pytest.fixture(name="probe_urlconf")
def probe_urlconf_fixture(settings):
    settings.ROOT_URLCONF = "euphro_auth.tests.test_mfa"


def _bearer(token) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _refresh_token(user, mfa):
    refresh = EuphroRefreshToken.for_user(user)
    if mfa is not None:
        refresh["mfa"] = mfa
    return refresh


@pytest.mark.parametrize(
    "is_admin,mfa,expected",
    [
        # SessionAuthentication comes first in DRF's defaults, so DRF answers
        # authentication failures with 403 instead of 401.
        (True, False, 403),
        (True, True, 200),
        (True, None, 200),  # issued before MFA: accepted until expiry
        (False, False, 200),
    ],
)
@pytest.mark.usefixtures("probe_urlconf")
def test_jwt_authentication_enforces_mfa_claim_for_admins(is_admin, mfa, expected):
    user = StaffUserFactory(is_lab_admin=is_admin)
    access = _refresh_token(user, mfa).access_token
    response = Client().get(PROBE_URL, **_bearer(access))
    assert response.status_code == expected


@pytest.mark.usefixtures("probe_urlconf")
def test_jwt_without_mfa_refused_after_promotion_to_admin():
    user = StaffUserFactory()
    access = _refresh_token(user, False).access_token
    assert Client().get(PROBE_URL, **_bearer(access)).status_code == 200
    user.is_lab_admin = True
    user.save()
    response = Client().get(PROBE_URL, **_bearer(access))
    assert response.status_code == 403
    assert response.json()["code"] == "mfa_required"


@pytest.mark.usefixtures("probe_urlconf")
def test_jwt_without_mfa_accepted_for_admin_when_mfa_disabled(settings):
    settings.MFA_ADMIN_REQUIRED = False
    access = _refresh_token(LabAdminUserFactory(), False).access_token
    assert Client().get(PROBE_URL, **_bearer(access)).status_code == 200


@pytest.mark.parametrize(
    "is_admin,mfa,expected",
    [
        (True, False, 401),
        (True, True, 200),
        (True, None, 200),
        (False, False, 200),
    ],
)
def test_refresh_enforces_mfa_claim_for_admins(is_admin, mfa, expected, caplog):
    user = StaffUserFactory(is_lab_admin=is_admin)
    with caplog.at_level(logging.WARNING, logger="euphro_auth.jwt.serializers"):
        response = Client().post(
            "/api/auth/token/refresh/",
            {"refresh": str(_refresh_token(user, mfa))},
            content_type="application/json",
        )
    assert response.status_code == expected
    if expected == 401:
        assert response.json()["code"] == "mfa_required"
        assert "Token refresh refused" in caplog.text
