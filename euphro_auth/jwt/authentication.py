from datetime import timedelta
from functools import cache

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token

from ..models import User


@cache
def _backend_token_backend() -> TokenBackend:
    return TokenBackend("HS256", settings.TOOLS_API_BACKEND_TOKEN_SECRET)


class EuphrosyneBackendToken(Token):
    """
    Token the Tools API signs to call Euphrosyne. It is signed with a secret
    dedicated to this channel, not with the key of the tokens Euphrosyne issues.
    """

    token_type = "euphrosyne_backend"
    lifetime = timedelta(minutes=5)

    @property
    def token_backend(self) -> TokenBackend:  # type: ignore[override]
        return _backend_token_backend()

    @classmethod
    def for_euphrosyne(cls) -> "EuphrosyneBackendToken":
        """Build the token the Tools API sends (used by tests)."""
        token = cls()
        token[api_settings.USER_ID_CLAIM] = "euphrosyne"
        return token

    def verify(self) -> None:
        # Subclass to remove JTI_CLAIM and token type check
        self.check_exp()


class EuphrosyneAdminJWTAuthentication(JWTAuthentication):
    """Used to authenticate "euphrosyne" admin user in backend-to-backend communication.
    For example when reiceiving data requests from Euphro Tools."""

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as error:
            raise InvalidToken(
                "Token contained no recognizable user identification"
            ) from error

        if user_id != "euphrosyne":
            raise AuthenticationFailed("Invalid user identification")

        user = User(email="euphrosyne", is_lab_admin=True)

        return user

    def get_validated_token(self, raw_token: bytes) -> Token:
        messages = []
        try:
            return EuphrosyneBackendToken(raw_token)  # type: ignore
        except TokenError as e:
            messages.append(
                {
                    "token_class": EuphrosyneBackendToken.__name__,
                    "token_type": EuphrosyneBackendToken.token_type,
                    "message": e.args[0],
                }
            )

        raise InvalidToken(
            {
                "detail": "Given token not valid for "
                f"{EuphrosyneBackendToken.token_type} type",
                "messages": messages,
            }
        )
