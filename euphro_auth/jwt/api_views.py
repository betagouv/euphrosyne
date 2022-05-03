from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.views import TokenViewBase

from .serializers import SessionTokenObtainSerializer


class SessionTokenObtainPairView(TokenViewBase):
    """
    Takes an authenticated request and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]  # permission to user with `is_staff`
    serializer_class = SessionTokenObtainSerializer
