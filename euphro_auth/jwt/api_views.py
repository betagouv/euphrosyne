from drf_spectacular.utils import extend_schema
from rest_framework import authentication
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.views import TokenViewBase

from .serializers import (
    SessionAccessTokenResponseSerializer,
    SessionAccessTokenSerializer,
)


class SessionAccessTokenView(TokenViewBase):
    """
    Takes a request authenticated by the web session and returns an access
    JSON web token. No password is accepted here and no refresh token is
    returned: ask this view again for a new access token.
    """

    authentication_classes = (  # type: ignore[assignment]
        authentication.SessionAuthentication,
    )
    permission_classes = (  # type: ignore[assignment]
        IsAdminUser,
    )  # permission to user with `is_staff`
    serializer_class = SessionAccessTokenSerializer  # type: ignore[assignment]

    @extend_schema(request=None, responses=SessionAccessTokenResponseSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
