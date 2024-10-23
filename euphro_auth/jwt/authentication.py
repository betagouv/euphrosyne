from datetime import timedelta

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token

from ..models import User


class EuphrosyneBackendToken(Token):
    """
    Custom token class for Euphrosyne backend communication.
    """

    token_type = "euphrosyne_backend"
    lifetime = timedelta(minutes=5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            return EuphrosyneBackendToken(raw_token)
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
