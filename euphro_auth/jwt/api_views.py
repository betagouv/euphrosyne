from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import authentication
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.views import TokenViewBase

from .serializers import (
    LoginLockoutSerializer,
    LongTokenObtainSerializer,
    SessionTokenObtainSerializer,
    TokenPairResponseSerializer,
)

token_response_schema = extend_schema_view(
    post=extend_schema(
        responses={200: TokenPairResponseSerializer, 429: LoginLockoutSerializer},
        parameters=[
            OpenApiParameter(
                "Retry-After",
                int,
                OpenApiParameter.HEADER,
                description="Seconds remaining before password authentication resumes.",
                response=[429],
            )
        ],
    )
)


@token_response_schema
class SessionTokenObtainPairView(TokenViewBase):
    """
    Takes an authenticated request and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    authentication_classes = (  # type: ignore[assignment]
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
    )
    permission_classes = (  # type: ignore[assignment]
        IsAdminUser,
    )  # permission to user with `is_staff`
    serializer_class = SessionTokenObtainSerializer  # type: ignore[assignment]


@token_response_schema
class LongTokenOptainPairView(TokenViewBase):
    """
    Takes an authenticated request and returns a long-lived access and refresh
    JSON web token pair to prove the authentication of those credentials.
    """

    authentication_classes = (  # type: ignore[assignment]
        authentication.BasicAuthentication,
    )
    permission_classes = ()
    serializer_class = LongTokenObtainSerializer  # type: ignore[assignment]
