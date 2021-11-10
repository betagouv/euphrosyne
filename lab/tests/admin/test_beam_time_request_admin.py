from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import UserGroups

from ...models import (
    BeamTimeRequest,
    BeamTimeRequestFormType,
    BeamTimeRequestType,
    Project,
)


class TestBeamTimeRequestAdminViewAsParticipant(TestCase):
    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="participant@test.com", password="password", is_staff=True
        )
        self.participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.project = Project.objects.create(name="Project Test")
        self.project.participation_set.create(
            user=self.participant_user, is_leader=False
        )
        self.client.force_login(self.participant_user)

    def test_add_beam_time_request_is_forbidden(self):
        response = self.client.post(
            reverse("admin:lab_beamtimerequest_add"),
            data={"request_type": BeamTimeRequestType.FRENCH.value},
        )

        assert response.status_code == 403

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


class TestBeamTimeRequestAdminViewAsLeader(TestCase):
    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="participant@test.com", password="password", is_staff=True
        )
        self.participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.project = Project.objects.create(name="Project Test")
        self.project.participation_set.create(
            user=self.participant_user, is_leader=True
        )
        self.client.force_login(self.participant_user)

    def test_add_beam_time_request_is_forbidden(self):
        response = self.client.post(
            reverse("admin:lab_beamtimerequest_add"),
            data={"request_type": BeamTimeRequestType.FRENCH.value},
        )

        assert response.status_code == 403

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


class TestBeamTimeRequestAdminViewAsAdmin(TestCase):
    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.participant_user = get_user_model().objects.create_user(
            email="admin@test.com", password="password", is_staff=True
        )
        self.participant_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))
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
