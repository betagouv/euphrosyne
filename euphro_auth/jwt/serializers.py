from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings

from .tokens import EuphroRefreshToken


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

        refresh = self.token_class.for_user(self.user)

        return {"access": str(refresh.access_token)}


class SessionAccessTokenResponseSerializer(serializers.Serializer):
    """OpenAPI description of the session access token response."""

    access = serializers.CharField(read_only=True)
