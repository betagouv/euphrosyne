from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.test import RequestFactory

from ..serializers import SessionTokenObtainSerializer


def test_validate_return_tokens():
    request = RequestFactory().post("/api/auth/token/")
    request.COOKIES["csrftoken"] = get_token(request)
    request.user = get_user_model()
    serializer = SessionTokenObtainSerializer()
    serializer.context["request"] = request

    data = serializer.validate(None)
    assert "refresh" in data
    assert "access" in data
