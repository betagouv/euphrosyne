import jwt
import pytest
from django.conf import settings as django_settings

from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory
from euphro_auth.tests.jwks import decode_with_jwks
from euphro_auth.tests.test_mfa import PASSWORD, enroll, sign_in
from lab.tests.factories import ParticipationFactory

from ..signing import eros_image_token, tools_api_backend_token

pytestmark = pytest.mark.django_db


@pytest.fixture(name="mfa_required", autouse=True)
def mfa_required_fixture(settings):
    settings.MFA_ADMIN_REQUIRED = True


def test_session_token_describes_the_user(client):
    participation = ParticipationFactory(user=StaffUserFactory())
    client.force_login(participation.user)

    response = client.post("/api/auth/token/")

    assert response.status_code == 200
    # Session clients get an access token only: no refresh token that would
    # outlive the session.
    assert set(response.json()) == {"access"}
    payload = decode_with_jwks(response.json()["access"])
    assert payload["sub"] == str(participation.user.pk)
    assert payload["scope"] == "tools"
    assert payload["token_use"] == "access"
    assert payload["client_id"] == "euphrosyne"
    assert payload["is_admin"] is False
    assert payload["projects"] == [
        {
            "id": participation.project.id,
            "name": participation.project.name,
            "slug": participation.project.slug,
        }
    ]
    lifetime = django_settings.IDP_OIDC_ACCESS_TOKEN_EXPIRES_IN
    assert payload["exp"] - payload["iat"] == lifetime


def test_verified_admin_session_token_carries_admin_rights(client):
    admin = LabAdminUserFactory()
    admin.set_password(PASSWORD)
    admin.save()
    sign_in(client, admin, enroll(admin))

    response = client.post("/api/auth/token/")

    assert response.status_code == 200
    assert decode_with_jwks(response.json()["access"])["is_admin"] is True


def test_backend_token_names_no_user():
    payload = decode_with_jwks(tools_api_backend_token())

    assert payload["scope"] == "tools:backend"
    assert payload["is_admin"] is True
    assert "sub" not in payload


def test_eros_image_token_names_no_user_and_grants_only_eros():
    payload = decode_with_jwks(eros_image_token())

    assert payload["scope"] == "tools:eros"
    assert "sub" not in payload
    assert "is_admin" not in payload


def test_tokens_are_not_signed_with_the_secret_key():
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(
            tools_api_backend_token(),
            django_settings.SECRET_KEY,
            algorithms=["HS256"],
        )
