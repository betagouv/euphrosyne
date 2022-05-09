from django.middleware.csrf import get_token
from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.state import token_backend

from lab.tests.factories import ParticipationFactory

from ..serializers import SessionTokenObtainSerializer


class TestSerializers(TestCase):
    @staticmethod
    def test_validate_return_tokens():
        participation = ParticipationFactory()
        request = RequestFactory().post("/api/auth/token/")
        request.COOKIES["csrftoken"] = get_token(request)
        request.user = participation.user
        serializer = SessionTokenObtainSerializer()
        serializer.context["request"] = request

        data = serializer.validate(None)
        assert "refresh" in data
        assert "access" in data
        decoded_token = token_backend.decode(data["access"])
        assert "projects" in decoded_token
        assert decoded_token["projects"][0]["id"] == participation.project.id
