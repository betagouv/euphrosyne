import base64
from io import StringIO
from urllib.parse import urlencode

import pytest
from allauth.idp.oidc.models import Client as OIDCClient
from django.conf import settings as django_settings
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from data_request.tests.factories import DataRequestFactory
from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from euphro_auth.tests.jwks import decode_with_jwks
from euphro_auth.tests.oidc import issue_access_token
from euphro_auth.tests.test_mfa import PASSWORD, enroll, sign_in

pytestmark = pytest.mark.django_db

DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
DEVICE_PAGE = "/identity/o/device"
TOKEN_URL = "/identity/o/api/token"


@pytest.fixture(autouse=True)
def oidc_clients(settings):
    settings.MFA_ADMIN_REQUIRED = True
    call_command("ensure_oidc_clients", stdout=StringIO())


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


def form_post(url: str, data: dict, **kwargs):
    """The OAuth endpoints only accept form-encoded bodies."""
    return Client().post(
        url,
        urlencode(data),
        content_type="application/x-www-form-urlencoded",
        **kwargs,
    )


def start_device_flow() -> dict:
    response = form_post(
        "/identity/o/api/device/code",
        {"client_id": django_settings.OIDC_HERMA_CLIENT_ID, "scope": "openid tools"},
    )
    assert response.status_code == 200
    return response.json()


def approve(client: Client, user_code: str, action: str = "confirm"):
    return client.post(f"{DEVICE_PAGE}?code={user_code}", {"action": action})


def poll(device_code: str):
    return form_post(
        TOKEN_URL,
        {
            "grant_type": DEVICE_GRANT,
            "device_code": device_code,
            "client_id": django_settings.OIDC_HERMA_CLIENT_ID,
        },
    )


def refresh(refresh_token: str):
    return form_post(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": django_settings.OIDC_HERMA_CLIENT_ID,
        },
    )


def test_admin_authorizes_herma(verified_client, admin_user):
    device = start_device_flow()
    assert device["verification_uri"].endswith(DEVICE_PAGE)

    page = verified_client.get(f"{DEVICE_PAGE}?code={device['user_code']}")
    assert page.status_code == 200
    assert "Herma" in page.content.decode()
    assert approve(verified_client, device["user_code"]).status_code == 200

    tokens = poll(device["device_code"]).json()
    payload = decode_with_jwks(tokens["access_token"])
    assert payload["sub"] == str(admin_user.pk)
    assert payload["client_id"] == django_settings.OIDC_HERMA_CLIENT_ID
    assert payload["token_use"] == "access"
    assert set(payload["scope"].split()) == {"openid", "tools"}
    assert payload["is_admin"] is True
    assert payload["projects"] == []
    # Herma also calls Euphrosyne's API with its token.
    response = Client().get(
        "/api/lab/projects/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200


def test_denied_device_gets_no_token(verified_client):
    device = start_device_flow()

    approve(verified_client, device["user_code"], action="deny")

    assert poll(device["device_code"]).json()["error"] == "access_denied"


def test_refresh_recomputes_admin_rights_and_rotates(verified_client, admin_user):
    device = start_device_flow()
    approve(verified_client, device["user_code"])
    tokens = poll(device["device_code"]).json()
    admin_user.is_lab_admin = False
    admin_user.save()

    response = refresh(tokens["refresh_token"])

    assert response.status_code == 200
    assert decode_with_jwks(response.json()["access_token"])["is_admin"] is False
    assert refresh(tokens["refresh_token"]).status_code == 400


def test_herma_is_reserved_to_administrators(client):
    client.force_login(StaffUserFactory())
    device = start_device_flow()

    response = client.get(f"{DEVICE_PAGE}?code={device['user_code']}")

    assert response.status_code == 403
    assert approve(client, device["user_code"]).status_code == 403
    assert poll(device["device_code"]).json()["error"] == "authorization_pending"


def test_admin_needs_a_verified_session(client, admin_user):
    client.force_login(admin_user)
    device = start_device_flow()

    response = client.get(f"{DEVICE_PAGE}?code={device['user_code']}")

    assert response.status_code == 302
    assert response.url.startswith(reverse("mfa_activate_totp"))


def test_device_page_needs_a_signed_in_user(client):
    response = client.get(DEVICE_PAGE)

    assert response.status_code == 302
    assert response.url.startswith("/login/")


def test_approval_needs_a_csrf_token(settings, admin_user):
    settings.MFA_ADMIN_REQUIRED = False
    client = Client(enforce_csrf_checks=True)
    client.force_login(admin_user)
    device = start_device_flow()

    page = client.get(f"{DEVICE_PAGE}?code={device['user_code']}")
    assert 'name="csrfmiddlewaretoken"' in page.content.decode()
    assert approve(client, device["user_code"]).status_code == 403

    response = client.post(
        f"{DEVICE_PAGE}?code={device['user_code']}",
        {"action": "confirm", "csrfmiddlewaretoken": page.context["csrf_token"]},
    )
    assert response.status_code == 200
    assert "access_token" in poll(device["device_code"]).json()


def test_tools_api_calls_euphrosyne_with_client_credentials():
    tools_api = OIDCClient.objects.get(id=django_settings.OIDC_TOOLS_API_CLIENT_ID)
    tools_api.set_secret("tools-api-secret")
    tools_api.save()
    credentials = base64.b64encode(
        f"{django_settings.OIDC_TOOLS_API_CLIENT_ID}:tools-api-secret".encode()
    ).decode()

    response = form_post(
        TOKEN_URL,
        {"grant_type": "client_credentials", "scope": "euphrosyne:backend"},
        headers={"Authorization": f"Basic {credentials}"},
    )

    token = response.json()["access_token"]
    assert "sub" not in decode_with_jwks(token)
    data_request = DataRequestFactory()
    response = Client().post(
        "/api/data-request/access-event",
        {"data_request": data_request.id, "path": "test/path"},
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )
    assert response.status_code == 201


def test_tools_api_token_without_the_backend_scope_is_refused():
    token = issue_access_token(django_settings.OIDC_TOOLS_API_CLIENT_ID, scopes=[])

    response = Client().post(
        "/api/data-request/access-event",
        {"data_request": DataRequestFactory().id, "path": "test/path"},
        headers={"Authorization": f"Bearer {token}"},
        content_type="application/json",
    )

    assert response.status_code == 401


def _tools_api_client() -> OIDCClient:
    return OIDCClient.objects.get(id=django_settings.OIDC_TOOLS_API_CLIENT_ID)


def test_ensure_oidc_clients_sets_the_tools_api_secret(settings):
    settings.OIDC_TOOLS_API_CLIENT_SECRET = "first-secret"
    call_command("ensure_oidc_clients", stdout=StringIO())
    assert _tools_api_client().check_secret("first-secret")

    # Rotation: a new value replaces the old one.
    settings.OIDC_TOOLS_API_CLIENT_SECRET = "second-secret"
    call_command("ensure_oidc_clients", stdout=StringIO())
    tools_api = _tools_api_client()
    assert tools_api.check_secret("second-secret")
    assert not tools_api.check_secret("first-secret")


def test_ensure_oidc_clients_keeps_the_secret_when_none_is_configured(settings):
    settings.OIDC_TOOLS_API_CLIENT_SECRET = ""
    tools_api = _tools_api_client()
    tools_api.set_secret("tools-api-secret")
    tools_api.save()

    call_command("ensure_oidc_clients", stdout=StringIO())

    assert OIDCClient.objects.count() == 2
    tools_api.refresh_from_db()
    assert tools_api.check_secret("tools-api-secret")
    herma = OIDCClient.objects.get(id=django_settings.OIDC_HERMA_CLIENT_ID)
    assert herma.type == OIDCClient.Type.PUBLIC
    assert herma.get_grant_types() == [DEVICE_GRANT, "refresh_token"]
