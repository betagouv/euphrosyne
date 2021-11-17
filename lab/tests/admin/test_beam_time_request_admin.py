from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ...models import (
    BeamTimeRequest,
    BeamTimeRequestFormType,
    BeamTimeRequestType,
    Project,
)


class TestBeamTimeRequestAdminViewAsAdmin(TestCase):
    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
            is_lab_admin=True,
        )
        self.client.force_login(self.participant_user)
        self.project = Project.objects.create(name="Project Test")

    def test_change_beam_time_request_is_ignored(self):
        beam_time_request = BeamTimeRequest.objects.create(
            project=self.project, request_type=BeamTimeRequestType.FRENCH.value
        )
        response = self.client.post(
            reverse("admin:lab_beamtimerequest_change", args=[beam_time_request.id]),
            data={
                "request_type": BeamTimeRequestType.EUROPEAN.value,
                "request_id": "ID",
                "problem_statement": "To be or not to be ?",
                "form_type": BeamTimeRequestFormType.SCIENCESCALL.value,
            },
        )
        beam_time_request.refresh_from_db()

        assert response.status_code == 302
        assert beam_time_request.request_type == BeamTimeRequestType.FRENCH.value

    def test_delete_beam_time_request_is_forbidden(self):
        beam_time_request = BeamTimeRequest.objects.create(
            project=self.project, request_type=BeamTimeRequestType.FRENCH.value
        )
        response = self.client.post(
            reverse("admin:lab_beamtimerequest_delete", args=[beam_time_request.id]),
        )

        assert response.status_code == 403

    def test_add_beam_time_request_is_forbidden(self):
        response = self.client.post(
            reverse("admin:lab_beamtimerequest_add"),
            data={"request_type": BeamTimeRequestType.FRENCH.value},
        )

        assert response.status_code == 403
