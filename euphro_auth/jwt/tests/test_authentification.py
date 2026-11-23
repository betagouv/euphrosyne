import jwt
import pytest
from django.conf import settings
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

from ...tests import factories
from ..authentication import EuphrosyneAdminJWTAuthentication, EuphrosyneBackendToken
from ..tokens import EuphroToolsAPIToken


def _tools_api_token(key: str, algorithm: str = "HS256") -> bytes:
    """A token as the Tools API signs it (generate_token_for_euphrosyne_backend)."""
    return jwt.encode(
        {"user_id": "euphrosyne", "exp": 9999999999}, key, algorithm=algorithm
    ).encode()


@pytest.mark.django_db
def test_euphrosyne_admin_jwt_authentication():
    auth = EuphrosyneAdminJWTAuthentication()

    assert auth.get_user(EuphrosyneBackendToken.for_euphrosyne())

    with pytest.raises(AuthenticationFailed):
        auth.get_user(EuphrosyneBackendToken.for_user(factories.StaffUserFactory()))


def test_backend_token_signed_with_the_dedicated_secret_is_accepted():
    auth = EuphrosyneAdminJWTAuthentication()
    token = _tools_api_token(settings.TOOLS_API_BACKEND_TOKEN_SECRET)

    assert auth.get_validated_token(token)["user_id"] == "euphrosyne"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(
            lambda: _tools_api_token(settings.SECRET_KEY), id="signed-with-secret-key"
        ),
        pytest.param(
            lambda: str(EuphroToolsAPIToken.for_euphrosyne().access_token).encode(),
            id="issued-by-euphrosyne",
        ),
    ],
)
def test_backend_token_not_signed_with_the_dedicated_secret_is_rejected(token):
    with pytest.raises(InvalidToken):
        EuphrosyneAdminJWTAuthentication().get_validated_token(token())
