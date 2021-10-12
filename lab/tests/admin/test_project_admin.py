from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import User, UserGroups

from ...models import Participation, Project


def get_add_participation_post_data(
    project: Project, new_member: User, leader_participation: Participation
):
    return {
        "name": "some project name",
        "leader": project.leader_id,
        "participation_set-0-user": project.leader_id,
        "participation_set-0-project": project.id,
        "participation_set-0-id": leader_participation.id,
        "participation_set-1-user": new_member.id,
        "participation_set-1-project": project.id,
        "participation_set-1-id": "",
        "participation_set-TOTAL_FORMS": "5",
        "participation_set-INITIAL_FORMS": "1",
        "participation_set-__prefix__-id": "",
        "participation_set-__prefix__-project": "2",
        "participation_set-__prefix__-user": "",
    }


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
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
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
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
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
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "some other project name"
        assert project.leader_id == self.project_participant_user.id

    def test_can_view_all_projects(self):
        Project.objects.create(
            name="other project 1", leader=self.project_participant_user
        )
        Project.objects.create(
            name="other project 2", leader=self.project_participant_user
        )
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "other project 1" in response.content.decode()
        assert "other project 2" in response.content.decode()

    def test_add_participations_is_allowed(self):
        project = Project.objects.create(
            name="some project name", leader=self.project_participant_user
        )
        project.members.add(self.project_participant_user)
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data=get_add_participation_post_data(
                project=project,
                new_member=member,
                leader_participation=project.participation_set.first(),
            ),
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.members.count() == 2
        assert project.members.last().id == member.id


class TestProjectAdminViewAsProjectLeader(TestCase):

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
        self.project_leader = get_user_model().objects.create_user(
            email="leader@test.com",
            password="leader",
            is_staff=True,
        )
        self.project_leader.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.project = Project.objects.create(
            name="some project name", leader=self.project_leader
        )
        self.client.force_login(self.project_leader)

    def test_change_project_leader_is_ignored(self):
        "Test change project leader is ignored thanks to excluding leader field"
        change_view_url = reverse("admin:lab_project_change", args=[self.project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "leader": self.admin_user.id,
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.leader_id == self.project_leader.id

    def test_change_project_name_is_allowed(self):
        change_view_url = reverse("admin:lab_project_change", args=[self.project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.name == "some other project name"

    def test_cannot_view_other_projects(self):
        Project.objects.create(name="unviewable", leader=self.admin_user)
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "unviewable" not in response.content.decode()

    def test_add_participations_is_allowed(self):
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        self.project.members.add(self.project_leader)
        change_view_url = reverse("admin:lab_project_change", args=[self.project.id])
        response = self.client.post(
            change_view_url,
            data=get_add_participation_post_data(
                project=self.project,
                new_member=member,
                leader_participation=self.project.participation_set.first(),
            ),
        )
        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.members.count() == 2
        assert self.project.members.last().id == member.id


class TestProjectAdminViewAsProjectMember(TestCase):

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
        self.project_member = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.project_member.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.projects_with_member = [
            Project.objects.create(name="project foo", leader=self.admin_user),
            Project.objects.create(name="project bar", leader=self.admin_user),
        ]
        for project in self.projects_with_member:
            Participation.objects.create(user=self.project_member, project=project)
        self.client.force_login(self.project_member)

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
            data={
                "name": "some project name",
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        projects_as_leader_qs = Project.objects.filter(leader=self.project_member)
        assert projects_as_leader_qs.count() == 1
        assert projects_as_leader_qs[0].name == "some project name"
        assert projects_as_leader_qs[0].leader_id == self.project_member.id

    def test_add_project_adds_user_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "participation_set-TOTAL_FORMS": "5",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_member.id

    def test_can_view_projects(self):
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "project foo" in response.content.decode()
        assert "project bar" in response.content.decode()

    def test_can_view_project(self):
        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.projects_with_member[0].id])
        )
        assert response.status_code == 200
        assert (
            "<label>Project name\xc2\xa0:</label>\n \n "
            '<div class="readonly">{}</div>'.format(self.projects_with_member[0].name)
        )

    def test_add_participations_is_ignored(self):
        project = Project.objects.create(
            name="some project name", leader=self.admin_user
        )
        project.members.add(self.project_member)
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data=get_add_participation_post_data(
                project=project,
                new_member=member,
                leader_participation=project.participation_set.first(),
            ),
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_member.id
