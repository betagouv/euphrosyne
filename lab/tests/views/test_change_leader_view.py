from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from ...models import Project


class TestChangeLeaderView(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create(
            email="admin@test.test", is_staff=True, is_lab_admin=True
        )

        self.project = Project.objects.create(name="Test project")

        leader = get_user_model().objects.create(
            email="leader@test.test", is_staff=True
        )
        self.project.participation_set.create(
            user=leader,
            is_leader=True,
        )

        member = get_user_model().objects.create(email="member@test.test")
        self.member_participation = self.project.participation_set.create(
            user=member,
            is_leader=False,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_change_leader_succeeds(self):
        self.client.post(
            reverse(
                "admin:lab_project_leader_participation_change", args=[self.project.id]
            ),
            data={"leader_participation": self.member_participation.id},
        )
        self.project.refresh_from_db()
        assert self.project.leader.id == self.member_participation.id

    def test_change_leader_as_non_admin_is_forbidden(self):
        self.client.force_login(self.project.leader.user)
        response = self.client.post(
            reverse(
                "admin:lab_project_leader_participation_change", args=[self.project.id]
            ),
            data={"leader_participation": self.member_participation.id},
        )
        assert response.status_code == 403
