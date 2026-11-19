import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings

from ..mfa.services import is_verified
from ..models import User
from .authentication import is_token_refused_for_missing_mfa
from .tokens import EuphroRefreshToken

logger = logging.getLogger(__name__)


# pylint: disable=abstract-method
class SessionTokenObtainSerializer(TokenObtainSerializer):
    """Generate token based on session user"""

    token_class = EuphroRefreshToken
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = {}

    def validate(self, attrs):
        self.user = self.context["request"].user

        if not simplejwt_api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        refresh = self.get_token(self.user)
        # Session verified with a second factor (see euphro_auth.mfa).
        refresh["mfa"] = is_verified(self.user)

        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)


class MFAEnforcingTokenRefreshSerializer(TokenRefreshSerializer):
    """Refuse to refresh a non-MFA token of a (possibly newly promoted)
    administrator while MFA is enforced."""

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
            raise AuthenticationFailed(
                _(
                    "Administrator accounts must use two-factor authentication: "
                    "generate a Herma token from the Euphrosyne page "
                    "/herma-token/ and paste it into Herma."
                ),
                "mfa_required",
            )
        return super().validate(attrs)
