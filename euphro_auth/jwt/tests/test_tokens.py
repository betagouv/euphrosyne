import jwt
from django.conf import settings

from ..tokens import ErosImageToken, EuphroToolsAPIToken


def _decode(token) -> dict:
    return jwt.decode(
        str(token),
        settings.SIMPLE_JWT["VERIFYING_KEY"],
        algorithms=["RS256"],
        issuer=settings.SITE_URL,
    )


def test_euphrotools_api_token():
    assert (
        EuphroToolsAPIToken.for_euphrosyne().access_token.payload["user_id"]
        == "euphrosyne"
    )


def test_tokens_are_signed_with_the_rsa_key():
    token = str(EuphroToolsAPIToken.for_euphrosyne().access_token)

    assert jwt.get_unverified_header(token)["alg"] == "RS256"
    assert _decode(token)["user_id"] == "euphrosyne"


def test_tokens_are_not_signed_with_the_secret_key():
    token = str(EuphroToolsAPIToken.for_euphrosyne().access_token)

    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return
    raise AssertionError("token verified with SECRET_KEY")


def test_eros_image_token_names_no_user_and_grants_only_eros():
    payload = _decode(ErosImageToken.for_images())

    assert payload["scope"] == "tools:eros"
    assert payload["token_type"] == "access"
    assert "user_id" not in payload
    assert "is_admin" not in payload
