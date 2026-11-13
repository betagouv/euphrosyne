"""OpenAPI (drf-spectacular) extensions for Euphrosyne JWT authentication."""

from drf_spectacular.authentication import BasicScheme
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class EuphrosyneAdminJWTScheme(SimpleJWTScheme):
    """Bearer JWT used by Euphrosyne backends (e.g. Tools API) to call the
    platform as the "euphrosyne" service account."""

    target_class = "euphro_auth.jwt.authentication.EuphrosyneAdminJWTAuthentication"
    name = "euphrosyneBackendJwtAuth"


class PasswordBasicScheme(BasicScheme):
    target_class = "euphro_auth.jwt.authentication.PasswordBasicAuthentication"
