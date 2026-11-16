import logging

from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings

from ..mfa.services import is_session_verified
from ..models import User
from .authentication import MFA_REQUIRED_MESSAGE, is_token_refused_for_missing_mfa
from .tokens import EuphroRefreshToken

logger = logging.getLogger(__name__)


# pylint: disable=abstract-method
class SessionAccessTokenSerializer(TokenObtainSerializer):
    """Generate an access token for the session user. No refresh token is
    returned: session clients get a new access token from their session, so a
    token does not outlive the session (logout, next user of the browser)."""

    token_class = EuphroRefreshToken
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {}

    def validate(self, attrs):
        request = self.context["request"]
        self.user = request.user

        if not simplejwt_api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        refresh = self.token_class.for_user(
            self.user, mfa=is_session_verified(request, self.user)
        )

        return {"access": str(refresh.access_token)}


class SessionAccessTokenResponseSerializer(serializers.Serializer):
    """OpenAPI description of the session access token response."""

    access = serializers.CharField(read_only=True)


class MFAEnforcingTokenRefreshSerializer(TokenRefreshSerializer):
    """Refuse to refresh an administrator's token issued without a second factor
    while MFA is enforced (including tokens issued before MFA)."""

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(simplejwt_api_settings.USER_ID_CLAIM)
        user = (
            User.objects.filter(**{simplejwt_api_settings.USER_ID_FIELD: user_id})
            .only("pk", "is_superuser", "is_lab_admin")
            .first()
            if user_id
            else None
        )
        if user is not None and is_token_refused_for_missing_mfa(user, refresh):
            logger.warning(
                "Token refresh refused for administrator %s: token without MFA",
                user.pk,
            )
            raise AuthenticationFailed(MFA_REQUIRED_MESSAGE, "mfa_required")
        return super().validate(attrs)
