from rest_framework import authentication
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.views import TokenRefreshView, TokenViewBase

from .serializers import (
    MFAEnforcingTokenRefreshSerializer,
    SessionTokenObtainSerializer,
)


class SessionTokenObtainPairView(TokenViewBase):
    """
    Takes an authenticated request and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    authentication_classes = (  # type: ignore[assignment]
        authentication.SessionAuthentication,
    )
    permission_classes = (  # type: ignore[assignment]
        IsAdminUser,
    )  # permission to user with `is_staff`
    serializer_class = SessionTokenObtainSerializer  # type: ignore[assignment]


class MFAEnforcingTokenRefreshView(TokenRefreshView):
    serializer_class = MFAEnforcingTokenRefreshSerializer  # type: ignore[assignment]
