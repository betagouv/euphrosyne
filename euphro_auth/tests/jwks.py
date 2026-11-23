"""Verify tokens as the Tools API does: with /.well-known/jwks.json."""

import jwt
from django.conf import settings
from django.test import Client


def decode_with_jwks(token: str) -> dict:
    kid = jwt.get_unverified_header(token)["kid"]
    jwks = Client().get("/.well-known/jwks.json").json()
    key = next(key for key in jwks["keys"] if key["kid"] == kid)
    return jwt.decode(
        token,
        jwt.PyJWK(key).key,
        algorithms=["RS256"],
        issuer=settings.SITE_URL.rstrip("/"),
        options={"require": ["exp", "iss"]},
    )
