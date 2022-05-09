from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.settings import api_settings as simplejwt_api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import User


class EuphroRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user: User):
        token = super().for_user(user)
        token["projects"] = list(user.project_set.values("id", "name"))
        return token


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

        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)
