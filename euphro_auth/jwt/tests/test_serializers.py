from django.contrib.sessions.backends.db import SessionStore
from django.middleware.csrf import get_token
from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.state import token_backend

from lab.tests.factories import ParticipationFactory

from ..serializers import SessionAccessTokenSerializer


class TestSerializers(TestCase):
    @staticmethod
    def test_validate_returns_an_access_token():
        participation = ParticipationFactory()
        request = RequestFactory().post("/api/auth/token/")
        request.COOKIES["csrftoken"] = get_token(request)
        request.user = participation.user
        request.session = SessionStore()
        serializer = SessionAccessTokenSerializer()
        serializer.context["request"] = request

        data = serializer.validate(None)
        assert set(data) == {"access"}
        decoded_token = token_backend.decode(data["access"])
        assert "projects" in decoded_token
        assert decoded_token["projects"][0]["id"] == participation.project.id
