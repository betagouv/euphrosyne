from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import UserGroups

from ...models import Institution


class TestInstitutionAdminViewAsParticipant(TestCase):
    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="participant@test.com", password="password", is_staff=True
        )
        self.participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.client.force_login(self.participant_user)

    def test_add_institution_is_allowed(self):
        response = self.client.post(
            reverse("admin:lab_institution_add"),
            data={"name": "Louvre", "country": "France"},
        )

        assert response.status_code == 302
        assert Institution.objects.all().count() == 1

    def test_change_institution_is_forbidden(self):
        institution = Institution.objects.create(name="Louvre", country="France")
        response = self.client.post(
            reverse("admin:lab_institution_change", args=[institution.id]),
            data={
                "name": "C2RMF",
            },
        )

        assert response.status_code == 403

    def test_delete_institution_is_forbidden(self):
        institution = Institution.objects.create(name="Louvre", country="France")
        response = self.client.post(
            reverse("admin:lab_institution_delete", args=[institution.id]),
        )

        assert response.status_code == 403


class TestInstitutionAdminViewAsAdmin(TestCase):
    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="admin@test.com", password="password", is_staff=True
        )
        self.participant_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))
        self.client.force_login(self.participant_user)

    def test_change_institution_is_allowed(self):
        institution = Institution.objects.create(name="Louvre", country="France")
        response = self.client.post(
            reverse("admin:lab_institution_change", args=[institution.id]),
            data={
                "name": "C2RMF",
            },
        )
        institution.refresh_from_db()

        assert response.status_code == 302
        assert institution.name == "C2RMF"

    def test_delete_institution_is_allowed(self):
        institution = Institution.objects.create(name="Louvre", country="France")
        response = self.client.post(
            reverse("admin:lab_institution_delete", args=[institution.id]),
        )

        assert response.status_code == 200
