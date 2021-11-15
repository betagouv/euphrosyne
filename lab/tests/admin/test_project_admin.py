from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.models import User, UserGroups

from ...models import BeamTimeRequestType, Institution, Participation, Project


def get_existing_particiation_post_data(index: int, participation: Participation):
    return {
        f"participation_set-{index}-user": participation.user_id,
        f"participation_set-{index}-project": participation.project_id,
        f"participation_set-{index}-id": participation.id,
        f"participation_set-{index}-is_leader": participation.is_leader,
        f"participation_set-{index}-institution": participation.institution_id,
    }


def get_add_participation_post_data(
    index: int, project: Project, user: User, is_leader: bool, institution: Institution
):
    return {
        f"participation_set-{index}-user": user.id,
        f"participation_set-{index}-project": project.id,
        f"participation_set-{index}-id": "",
        f"participation_set-{index}-is_leader": is_leader,
        f"participation_set-{index}-institution": institution.id,
    }


def get_empty_beam_time_request_post_data(project_id: int):
    return {
        "beamtimerequest-TOTAL_FORMS": "1",
        "beamtimerequest-INITIAL_FORMS": "0",
        "beamtimerequest-0-request_type": "",
        "beamtimerequest-0-request_id": "",
        "beamtimerequest-0-form_type": "",
        "beamtimerequest-0-problem_statement": "",
        "beamtimerequest-0-id": "",
        "beamtimerequest-0-project": project_id,
    }


class BaseTestCases:
    class BaseTestProjectAdmin(TestCase):
        fixtures = ["groups"]

        def setUp(self):
            self.client = Client()
            self.add_view_url = reverse("admin:lab_project_add")

            self.admin_user = get_user_model().objects.create_user(
                email="admin_user@test.com", password="admin_user", is_staff=True
            )
            self.admin_user.groups.add(Group.objects.get(name=UserGroups.ADMIN.value))

            self.base_institution = Institution.objects.create(
                name="Louvre", country="France"
            )


class TestProjectAdminViewAsAdminUser(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()

        self.project_participant_user = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.project_participant_user.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.client.force_login(self.admin_user)

    def test_add_project_form_has_leader_hidden_input(self):
        response = self.client.get(self.add_view_url)
        assert response.status_code == HTTPStatus.OK
        assert (
            '<input type="hidden" name="participation_set-0-is_leader" '
            'value="True" id="id_participation_set-0-is_leader">'
            in response.content.decode()
        )

    def test_add_project_allows_setting_any_user_as_leader(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "0",
                "participation_set-0-id": "",
                "participation_set-0-project": "",
                "participation_set-0-user": self.project_participant_user.id,
                "participation_set-0-is_leader": "True",
                "participation_set-0-institution": self.base_institution.id,
            },
        )
        assert response.status_code == 302
        assert Project.objects.all().count() == 1
        assert Project.objects.all()[0].name == "some project name"
        assert (
            Project.objects.all()[0].leader.user_id == self.project_participant_user.id
        )

    def test_add_project_set_admin_as_admin(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "participation_set-0-id": "",
                "participation_set-0-project": "",
                "participation_set-0-user": self.project_participant_user.id,
                "participation_set-0-institution": self.base_institution.id,
                "participation_set-0-is_leader": "True",
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.admin_id == self.admin_user.id

    def test_change_project_user_is_allowed(self):
        project = Project.objects.create(name="some project name")
        participation = project.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "participation_set-0-id": participation.id,
                "participation_set-0-project": project.id,
                "participation_set-0-user": self.project_participant_user.id,
                "participation_set-0-institution": self.base_institution.id,
                "participation_set-0-is_leader": "True",
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "1",
                **get_empty_beam_time_request_post_data(project_id=project.id),
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "some other project name"
        assert project.leader.user_id == self.project_participant_user.id

    def test_set_basic_information_fields_is_allowed(self):
        project = Project.objects.create(name="some project name")
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some project name",
                "leader": self.project_participant_user.id,
                "comments": "Ancient egypt mummies analysis",
                "participation_set-TOTAL_FORMS": "0",
                "participation_set-INITIAL_FORMS": "0",
                **get_empty_beam_time_request_post_data(project_id=project.id),
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.comments == "Ancient egypt mummies analysis"

    def test_can_view_all_projects(self):
        Project.objects.create(name="other project 1")
        Project.objects.create(name="other project 2")
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "other project 1" in response.content.decode()
        assert "other project 2" in response.content.decode()

    def test_add_participations_is_allowed(self):
        project = Project.objects.create(name="some project name")
        project.participation_set.create(
            user=self.project_participant_user,
            is_leader=True,
            institution=self.base_institution,
        )
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some project name",
                **get_existing_particiation_post_data(
                    index=0, participation=project.leader
                ),
                **get_add_participation_post_data(
                    index=1,
                    project=project,
                    user=member,
                    is_leader=False,
                    institution=self.base_institution,
                ),
                "participation_set-TOTAL_FORMS": "2",
                "participation_set-INITIAL_FORMS": "1",
                **get_empty_beam_time_request_post_data(project_id=project.id),
            },
        )
        assert response.status_code == 302
        project.refresh_from_db()
        assert project.members.count() == 2
        assert project.members.last().id == member.id

    def test_get_content_has_change_leader_link(self):
        project = Project.objects.create(name="some project name")
        project.participation_set.create(
            user=self.project_participant_user,
            is_leader=True,
            institution=self.base_institution,
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.get(change_view_url)

        assert "change-leader-link" in response.content.decode()


class TestProjectAdminViewAsProjectLeader(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()

        self.project_leader = get_user_model().objects.create_user(
            email="leader@test.com",
            password="leader",
            is_staff=True,
        )
        self.project_leader.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.project = Project.objects.create(name="some project name")
        self.leader_participation = self.project.participation_set.create(
            user=self.project_leader, is_leader=True, institution=self.base_institution
        )
        self.client.force_login(self.project_leader)

    def test_add_participations_is_allowed(self):
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        change_view_url = reverse("admin:lab_project_change", args=[self.project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some project name",
                **get_existing_particiation_post_data(
                    index=0, participation=self.project.leader
                ),
                **get_add_participation_post_data(
                    index=1,
                    project=self.project,
                    user=member,
                    is_leader=False,
                    institution=self.base_institution,
                ),
                "participation_set-TOTAL_FORMS": "2",
                "participation_set-INITIAL_FORMS": "1",
                **get_empty_beam_time_request_post_data(project_id=self.project.id),
            },
        )
        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.members.count() == 2
        assert self.project.members.last().id == member.id

    def test_change_leader_link_is_hidden(self):
        change_view_url = reverse("admin:lab_project_change", args=[self.project.id])
        response = self.client.get(change_view_url)

        assert "change-leader-link" not in response.content.decode()


class TestProjectAdminViewAsProjectMember(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()

        self.project_member = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.project_member.groups.add(
            Group.objects.get(name=UserGroups.PARTICIPANT.value)
        )
        self.projects_with_member = [
            Project.objects.create(name="project foo"),
            Project.objects.create(name="project bar"),
        ]
        for project in self.projects_with_member:
            project.participation_set.create(user=self.admin_user, is_leader=True)
            project.participation_set.create(user=self.project_member)
        self.client.force_login(self.project_member)

    def test_cannot_view_other_projects(self):
        project = Project.objects.create(name="unviewable")
        project.participation_set.create(user=self.admin_user, is_leader=True)
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "unviewable" not in response.content.decode()

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
            },
        )
        project = Project.objects.get(name="some project name")

        assert response.status_code == 302
        assert project.name == "some project name"
        assert project.leader.user_id == self.project_member.id

    def test_add_project_adds_user_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
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
        project = Project.objects.create(name="some project name")
        project.participation_set.create(
            user=self.admin_user, is_leader=True, institution=self.base_institution
        )
        member_participation = project.participation_set.create(
            user=self.project_member, institution=self.base_institution
        )
        member = get_user_model().objects.create_user(
            email="member@test.com", password="password"
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some project name",
                **get_existing_particiation_post_data(
                    index=0, participation=project.leader
                ),
                **get_existing_particiation_post_data(
                    index=1, participation=member_participation
                ),
                **get_add_participation_post_data(
                    index=2,
                    project=project,
                    user=member,
                    is_leader=False,
                    institution=self.base_institution,
                ),
                "participation_set-TOTAL_FORMS": "3",
                "participation_set-INITIAL_FORMS": "2",
                **get_empty_beam_time_request_post_data(project_id=project.id),
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 2
        assert project.members.get(id=self.admin_user.id)
        assert project.members.get(id=self.project_member.id)

    def test_add_beam_time_request_is_allowed(self):
        project = Project.objects.create(name="some project name")
        project.participation_set.create(
            user=self.admin_user, is_leader=True, institution=self.base_institution
        )
        member_participation = project.participation_set.create(
            user=self.project_member, institution=self.base_institution
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        response = self.client.post(
            change_view_url,
            data={
                "name": "some project name",
                **get_existing_particiation_post_data(
                    index=0, participation=project.leader
                ),
                **get_existing_particiation_post_data(
                    index=1, participation=member_participation
                ),
                "participation_set-TOTAL_FORMS": "2",
                "participation_set-INITIAL_FORMS": "2",
                "beamtimerequest-TOTAL_FORMS": "1",
                "beamtimerequest-INITIAL_FORMS": "0",
                "beamtimerequest-0-request_type": BeamTimeRequestType.FRENCH.value,
                "beamtimerequest-0-request_id": "",
                "beamtimerequest-0-form_type": "",
                "beamtimerequest-0-problem_statement": "",
                "beamtimerequest-0-id": "",
                "beamtimerequest-0-project": project.id,
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.beamtimerequest

    def test_change_project_name_and_comments_is_allowed(self):
        project = Project.objects.create(name="some project name")
        project.participation_set.create(
            user=self.admin_user, is_leader=True, institution=self.base_institution
        )
        project.participation_set.create(
            user=self.project_member, institution=self.base_institution
        )
        change_view_url = reverse("admin:lab_project_change", args=[project.id])

        response = self.client.post(
            change_view_url,
            data={
                "name": "some other project name",
                "comments": "Ancient egypt mummies analysis",
                **get_existing_particiation_post_data(
                    index=0, participation=project.leader
                ),
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "1",
                **get_empty_beam_time_request_post_data(project_id=project.id),
            },
        )
        project.refresh_from_db()

        assert response.status_code == 302
        assert project.name == "some other project name"
        assert project.comments == "Ancient egypt mummies analysis"
