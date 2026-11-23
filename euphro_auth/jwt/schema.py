"""OpenAPI (drf-spectacular) extensions for Euphrosyne token authentication."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class UserTokenScheme(OpenApiAuthenticationExtension):
    """OpenID Connect access token issued to a user (device flow)."""

    target_class = "euphro_auth.jwt.authentication.UserTokenAuthentication"
    name = "oidcUserToken"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}


class EuphrosyneBackendScheme(OpenApiAuthenticationExtension):
    """OpenID Connect access token of the Tools API (client credentials), to
    call the platform as the "euphrosyne" service account."""

    target_class = "euphro_auth.jwt.authentication.EuphrosyneBackendAuthentication"
    name = "euphrosyneBackendToken"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
