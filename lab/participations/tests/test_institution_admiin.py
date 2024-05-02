from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Institution


class TestInstitutionAdminViewAsParticipant(TestCase):
    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="participant@test.com", password="password", is_staff=True
        )
        self.client.force_login(self.participant_user)

    def test_add_institution_is_allowed(self):
        response = self.client.post(
            reverse("admin:lab_institution_add"),
            data={"name": "Louvre", "country": "France"},
        )

        assert response.status_code == 302
        assert Institution.objects.all().count() == 1
