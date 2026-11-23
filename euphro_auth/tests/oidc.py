"""Issue OpenID Connect access tokens in tests, as allauth stores them."""

import secrets
from datetime import timedelta
from io import StringIO

from allauth.idp.oidc.models import Token
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from ..jwt.authentication import EUPHROSYNE_BACKEND_SCOPE
from ..models import User


def issue_access_token(
    client_id: str, *, user: User | None = None, scopes: list[str] | None = None
) -> str:
    call_command("ensure_oidc_clients", stdout=StringIO())
    value = secrets.token_urlsafe(32)
    token = Token(
        type=Token.Type.ACCESS_TOKEN,
        client_id=client_id,
        user=user,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    token.set_value(value)
    token.set_scopes(scopes or [])
    token.save()
    return value


def tools_api_backend_token() -> str:
    """Token the Tools API gets with the client credentials grant."""
    return issue_access_token(
        settings.OIDC_TOOLS_API_CLIENT_ID, scopes=[EUPHROSYNE_BACKEND_SCOPE]
    )


def herma_token(user: User) -> str:
    """Token Herma gets with the device flow."""
    return issue_access_token(
        settings.OIDC_HERMA_CLIENT_ID, user=user, scopes=["openid", "tools"]
    )
