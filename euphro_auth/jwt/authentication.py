"""Authentication of the OpenID Connect access tokens Euphrosyne issued
(allauth.idp.oidc). Tokens are looked up in the database, so a revoked or
expired token is refused."""

from allauth.idp.oidc.contrib.rest_framework.authentication import (
    TokenAuthentication,
)
from django.conf import settings

from ..models import User

# Scope the Tools API client is granted to call Euphrosyne.
EUPHROSYNE_BACKEND_SCOPE = "euphrosyne:backend"


class _BearerTokenAuthentication(TokenAuthentication):
    def authenticate_header(self, request):
        # Answer 401 rather than 403 when the token is refused, so the caller
        # knows to get a new one.
        return 'Bearer realm="api"'


class UserTokenAuthentication(_BearerTokenAuthentication):
    """Tokens issued to a user, such as Herma's. Tokens without a user (client
    credentials) are left to EuphrosyneBackendAuthentication."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None or result[0] is None:
            return None
        return result


class EuphrosyneBackendAuthentication(_BearerTokenAuthentication):
    """Tools API calling Euphrosyne as the "euphrosyne" service account, with a
    client credentials token. For example when receiving data requests."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, token = result
        if (
            user is not None
            or token.client_id != settings.OIDC_TOOLS_API_CLIENT_ID
            or EUPHROSYNE_BACKEND_SCOPE not in token.get_scopes()
        ):
            return None
        return User(email="euphrosyne", is_lab_admin=True), token
