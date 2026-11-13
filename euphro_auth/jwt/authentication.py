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


def is_token_refused_for_missing_mfa(user, token) -> bool:
    """A token explicitly issued without MFA (``mfa`` claim present and False)
    is refused for a lab administrator while MFA is enforced. This covers users
    promoted after the token was issued and tokens issued during a rollback.
    Tokens without the claim (issued before MFA was deployed) are accepted
    until they expire."""
    return bool(
        settings.MFA_ADMIN_REQUIRED
        and token.get("mfa", None) is False
        and is_lab_admin(user)
    )


class MFAEnforcingJWTAuthentication(JWTAuthentication):
    """Default JWT authentication: refuse non-MFA tokens of administrators."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if is_token_refused_for_missing_mfa(user, validated_token):
            raise AuthenticationFailed(
                "Multi-factor authentication is required for administrators.",
                code="mfa_required",
            )
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
