from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import UserGroups

from ...models import Project


class TestProjectAdminViewAsAdminUser(TestCase):

    fixtures = ["groups"]

    def setUp(self):
        self.client = Client()
        self.add_view_url = reverse("admin:lab_project_add")
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com", password="admin_user", is_staff=True
        )
        self.admin_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))
        self.project_participant_user = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.project_participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.client.force_login(self.admin_user)

    def test_add_project_form_has_leader_dropdown(self):
        response = self.client.get(self.add_view_url)
        assert response.status_code == HTTPStatus.OK
        assert (
            '<select name="leader" required id="id_leader">'
            in response.content.decode()
        )

    def test_add_project_allows_setting_any_user_as_leader(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "leader": self.project_participant_user.id,
            },
        )
        assert response.status_code == 302
        assert Project.objects.all().count() == 1
        assert Project.objects.all()[0].name == "some project name"
        assert Project.objects.all()[0].leader_id == self.project_participant_user.id

    def test_add_project_adds_leader_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "leader": self.project_participant_user.id,
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_participant_user.id

    def test_change_project_user_is_allowed(self):
        project = Project.objects.create(
            name="some project name", leader=self.admin_user
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "leader": self.project_participant_user.id,
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "some other project name"
        assert project.leader_id == self.project_participant_user.id


class TestProjectAdminViewAsNormalUser(TestCase):

    fixtures = [
        "groups",
    ]

    def setUp(self):
        self.client = Client()
        self.add_view_url = reverse("admin:lab_project_add")
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com", password="admin_user", is_staff=True
        )
        self.admin_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))
        self.project_participant_user = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.project_participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.client.force_login(self.project_participant_user)

    def test_add_project_form_has_no_leader_dropdown(self):
        response = self.client.get(self.add_view_url)
        assert response.status_code == HTTPStatus.OK
        assert (
            '<select name="leader" required id="id_leader">'
            not in response.content.decode()
        )

    def test_add_project_sets_user_as_leader(self):
        response = self.client.post(
            self.add_view_url,
            data={"name": "some project name"},
        )
        assert response.status_code == 302
        assert Project.objects.all().count() == 1
        assert Project.objects.all()[0].name == "some project name"
        assert Project.objects.all()[0].leader_id == self.project_participant_user.id

    def test_add_project_adds_user_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={"name": "some project name"},
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_participant_user.id

    def test_change_project_leader_is_ignored(self):
        "Test change project leader is ignored thanks to excluding leader field"
        project = Project.objects.create(
            name="some project name", leader=self.project_participant_user
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "leader": self.admin_user.id,
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.leader_id == self.project_participant_user.id

    def test_change_project_name_is_allowed(self):
        project = Project.objects.create(
            name="some project name", leader=self.project_participant_user
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url, data={"name": "some other project name"}
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "some other project name"
