from drf_spectacular.utils import extend_schema
from rest_framework import authentication, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .signing import session_access_token


# pylint: disable=abstract-method
class SessionAccessTokenResponseSerializer(serializers.Serializer):
    """OpenAPI description of the session access token response."""

    access = serializers.CharField(read_only=True)


class SessionAccessTokenView(APIView):
    """
    Takes a request authenticated by the web session and returns an access
    JSON web token. No password is accepted here and no refresh token is
    returned: ask this view again for a new access token, so a token does not
    outlive the session (logout, next user of the browser).
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (IsAdminUser,)  # permission to user with `is_staff`

    @extend_schema(request=None, responses=SessionAccessTokenResponseSerializer)
    def post(self, request: Request) -> Response:
        return Response({"access": session_access_token(request.user)})
