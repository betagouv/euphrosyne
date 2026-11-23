"""Access tokens Euphrosyne signs itself, outside an OpenID Connect grant.

They are signed like allauth's OpenID Connect access tokens: same key, same
``kid``, same issuer and lifetime. The Tools API verifies all of them with
/.well-known/jwks.json.
"""

import time
import uuid
from typing import Any

import jwt
from allauth.idp.oidc import app_settings
from allauth.idp.oidc.adapter import get_adapter
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ..models import User
from .claims import user_claims
from .keys import key_id

# ``client_id`` of the tokens Euphrosyne issues to itself.
EUPHROSYNE_CLIENT_ID = "euphrosyne"
# Scope of the Tools API, for the web front end and Herma.
TOOLS_SCOPE = "tools"
# Euphrosyne calling the Tools API as a service.
TOOLS_BACKEND_SCOPE = "tools:backend"
# EROS images proxied by the Tools API (see lab.objects.providers.eros).
TOOLS_EROS_SCOPE = "tools:eros"


def sign_access_token(claims: dict[str, Any]) -> str:
    adapter = get_adapter()
    private_key = serialization.load_pem_private_key(
        adapter.get_signing_key().pem.encode(), password=None
    )
    assert isinstance(private_key, rsa.RSAPrivateKey)
    issued_at = int(time.time())
    payload = {
        "iss": adapter.get_issuer(),
        "iat": issued_at,
        "exp": issued_at + app_settings.ACCESS_TOKEN_EXPIRES_IN,
        "jti": uuid.uuid4().hex,
        "token_use": "access",
        "client_id": EUPHROSYNE_CLIENT_ID,
        **claims,
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": key_id(private_key.public_key())},
    )


def session_access_token(user: User) -> str:
    """Token of the web front end, for the session user."""
    return sign_access_token(
        {"sub": str(user.pk), "scope": TOOLS_SCOPE, **user_claims(user)}
    )


def tools_api_backend_token() -> str:
    """Token of Euphrosyne itself, to call the Tools API."""
    return sign_access_token(
        {"scope": TOOLS_BACKEND_SCOPE, "projects": [], "is_admin": True}
    )


def eros_image_token() -> str:
    """Token put in the URL of EROS images. The URL is shown to any user who
    sees the object, so the token names no user and grants nothing else."""
    return sign_access_token({"scope": TOOLS_EROS_SCOPE})
