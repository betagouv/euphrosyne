from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token

from lab.permissions import is_lab_admin

from ..models import User

MFA_REQUIRED_MESSAGE = "Multi-factor authentication is required for administrators."


def is_token_refused_for_missing_mfa(user: User, token) -> bool:
    """While MFA is enforced, an administrator's token is accepted only when it
    was issued after a second factor (``mfa`` claim exactly True). This also
    refuses tokens issued before MFA, which have no such claim."""
    return bool(
        settings.MFA_ADMIN_REQUIRED
        and is_lab_admin(user)
        and token.get("mfa", None) is not True
    )


class MFAEnforcingJWTAuthentication(JWTAuthentication):
    """Default JWT authentication: refuse administrators' tokens without MFA."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if is_token_refused_for_missing_mfa(user, validated_token):
            raise AuthenticationFailed(MFA_REQUIRED_MESSAGE, code="mfa_required")
        return user


class EuphrosyneBackendToken(Token):
    """
    Custom token class for Euphrosyne backend communication.
    """

    token_type = "euphrosyne_backend"
    lifetime = timedelta(minutes=5)

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
