from http import HTTPStatus
from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from lab.models import Institution
from lab.tests.factories import (
    LabAdminUserFactory,
    ProjectFactory,
    ProjectWithLeaderFactory,
    RunFactory,
    StaffUserFactory,
)

from ..admin import ProjectAdmin, ProjectChangeList
from ..inlines import (
    BeamTimeRequestInline,
    LeaderParticipationInline,
    OnPremisesParticipationInline,
    RemoteParticipationInline,
)
from ..models import Project


class BaseTestCases:
    # pylint: disable=too-many-instance-attributes
    class BaseTestProjectAdmin(TestCase):
        def setUp(self):
            self.client = Client()
            self.add_view_url = reverse("admin:lab_project_add")
            self.request_factory = RequestFactory()

            self.admin_user = LabAdminUserFactory(
                email="admin_user@test.com",
                password="admin_user",
            )

            self.base_institution = Institution.objects.create(
                name="Louvre", country="France"
            )

            self.change_project = ProjectFactory()
            self.project_admin = ProjectAdmin(model=Project, admin_site=AdminSite())
            self.change_request = RequestFactory().get(
                reverse("admin:lab_project_change", args=[self.change_project.id])
            )
            self.add_request = RequestFactory().get(self.add_view_url)


class TestProjectAdminViewAsAdminUser(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()

        self.project_participant_user = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.client.force_login(self.admin_user)
        self.change_request.user = self.admin_user
        self.add_request.user = self.admin_user

    def test_create_project(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "confidential": True,
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "0",
                "participation_set-MIN_NUM_FORMS": "1",
                "participation_set-MAX_NUM_FORMS": "1000",
                "participation_set-0-id": "",
                "participation_set-0-project": "",
                "participation_set-0-user": self.project_participant_user.email,
                "participation_set-0-institution__name": "Louvre",
                "participation_set-0-institution__country": "France",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.confidential is True
        assert project.leader.user == self.project_participant_user

    def test_create_project_leader_mandatory(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "confidential": True,
                "participation_set-TOTAL_FORMS": "1",
                "participation_set-INITIAL_FORMS": "1",
                "participation_set-MIN_NUM_FORMS": "0",
                "participation_set-MAX_NUM_FORMS": "1000",
            },
        )
        assert response.status_code == 200
        assert response.context_data["inline_admin_formsets"][0].formset.forms[0].errors
        assert not Project.objects.filter(name="some project name").exists()

    def test_add_project_set_admin_as_admin(self):
        project = Project.objects.create(name="some project name")
        change_view_url = reverse("admin:lab_project_change", args=[project.id])
        request = self.request_factory.get(change_view_url)
        request.user = self.admin_user
        admin = ProjectAdmin(Project, admin_site=AdminSite())
        admin_form = admin.get_form(request, project, change=False)
        admin.save_model(request, project, admin_form, change=False)
        assert project.admin == self.admin_user

    def test_can_view_all_projects(self):
        Project.objects.create(name="other project 1")
        Project.objects.create(name="other project 2")
        response = self.client.get(reverse("admin:lab_project_changelist"))
        assert response.status_code == 200
        assert "other project 1" in response.content.decode()
        assert "other project 2" in response.content.decode()

    def test_participation_inlines_are_present_in_changeview(self):
        inlines = self.project_admin.get_inlines(
            self.change_request, self.change_project
        )
        assert LeaderParticipationInline in inlines
        assert OnPremisesParticipationInline in inlines
        assert RemoteParticipationInline in inlines

    def test_leader_participation_inline_present_in_create_changeview(self):
        inlines = self.project_admin.get_inlines(self.add_request)
        assert LeaderParticipationInline in inlines

    def test_name_is_readonly_when_change(self):
        assert "name" in self.project_admin.get_readonly_fields(
            self.change_request, self.change_project
        )

    def test_add_project_form_has_confidential_checkbox(self):
        response = self.client.get(self.add_view_url)
        assert '<input type="checkbox" name="confidential"' in response.content.decode()

    def test_change_project_form_has_confidential_checkbox(self):
        fieldsets = self.project_admin.get_fieldsets(
            self.change_request, self.change_project
        )
        assert "confidential" in fieldsets[0][1]["fields"]

    def test_add_project_has_not_cgu_checkbox(self):
        fieldsets = self.project_admin.get_fieldsets(self.add_request)
        assert len(fieldsets) == 1

    def test_participation_inlines(self):
        project = ProjectFactory()
        on_premises_user = StaffUserFactory(email="aneweuser@mail.com")
        remote_user = StaffUserFactory(email="remote@mail.com")

        participation_data = {
            "participation_set-TOTAL_FORMS": "1",
            "participation_set-INITIAL_FORMS": "0",
            "participation_set-MIN_NUM_FORMS": "1",
            "participation_set-MAX_NUM_FORMS": "1000",
            "participation_set-0-id": "",
            "participation_set-0-project": project.id,
            "participation_set-0-user": self.project_participant_user.email,
            "participation_set-0-institution__name": "Louvre",
            "participation_set-0-institution__country": "France",
            "participation_set-2-TOTAL_FORMS": "1",
            "participation_set-2-INITIAL_FORMS": "0",
            "participation_set-2-MIN_NUM_FORMS": "0",
            "participation_set-2-MAX_NUM_FORMS": "1000",
            "participation_set-2-0-id": "",
            "participation_set-2-0-project": project.id,
            "participation_set-2-0-user": on_premises_user.email,
            "participation_set-2-0-institution__name": "C2RMF",
            "participation_set-2-0-institution__country": "France",
            "participation_set-3-TOTAL_FORMS": "1",
            "participation_set-3-INITIAL_FORMS": "0",
            "participation_set-3-MIN_NUM_FORMS": "0",
            "participation_set-3-MAX_NUM_FORMS": "1000",
            "participation_set-3-0-id": "",
            "participation_set-3-0-project": project.id,
            "participation_set-3-0-user": remote_user.email,
            "participation_set-3-0-institution__name": "LMRH",
            "participation_set-3-0-institution__country": "France",
            # beamtime is mandatory
            "beamtimerequest-TOTAL_FORMS": "1",
            "beamtimerequest-INITIAL_FORMS": "0",
            "beamtimerequest-MIN_NUM_FORMS": "0",
            "beamtimerequest-MAX_NUM_FORMS": "1",
            "beamtimerequest-0-request_type": "C2RMF",
            "beamtimerequest-0-request_id": "",
            "beamtimerequest-0-form_type": "",
            "beamtimerequest-0-problem_statement": "problem statement",
            "beamtimerequest-0-id": "",
            "beamtimerequest-0-project": project.id,
        }
        response = self.client.post(
            reverse("admin:lab_project_change", args=[project.id]),
            data=participation_data,
        )

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.leader.user == self.project_participant_user

        assert project.participation_set.count() == 3
        assert (
            project.participation_set.get(on_premises=True, is_leader=False).user
            == on_premises_user
        )
        assert (
            project.participation_set.get(on_premises=False, is_leader=False).user
            == remote_user
        )


class TestProjectAdminViewAsProjectLeader(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()
        self.project_leader = get_user_model().objects.create_user(
            email="leader@test.com",
            password="leader",
            is_staff=True,
        )
        self.leader_participation = self.change_project.participation_set.create(
            user=self.project_leader, is_leader=True, institution=self.base_institution
        )
        self.client.force_login(self.project_leader)
        self.change_request.user = self.project_leader
        self.add_request.user = self.project_leader

    def test_participation_inline_is_present_in_changeview(self):
        inlines = self.project_admin.get_inlines(
            self.change_request, self.change_project
        )
        assert LeaderParticipationInline in inlines
        assert OnPremisesParticipationInline in inlines
        assert RemoteParticipationInline in inlines

    def test_leader_participation_inline_absent_in_create_changeview(self):
        inlines = self.project_admin.get_inlines(self.add_request)
        assert LeaderParticipationInline not in inlines

    def test_create_project(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
            },
        )
        assert response.status_code == 302
        assert Project.objects.get(name="some project name")

    def test_create_project_should_accept_cgu(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
            },
        )
        assert response.status_code == 200
        assert not Project.objects.filter(name="some project name").exists()

    def test_change_leader_link_is_hidden(self):
        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.change_project.id])
        )

        assert "change-leader-link" not in response.content.decode()

    def test_add_project_form_has_not_confidential_checkbox(self):
        response = self.client.get(self.add_view_url)
        assert (
            '<input type="checkbox" name="confidential" id="id_confidential">'
            not in response.content.decode()
        )

    def test_change_project_form_has_not_confidential_checkbox(self):
        fieldsets = self.project_admin.get_fieldsets(
            self.change_request, self.change_project
        )
        assert "confidential" not in fieldsets[0][1]["fields"]

    def test_add_project_has_cgu_checkbox(self):
        fieldsets = self.project_admin.get_fieldsets(self.add_request)
        assert "has_accepted_cgu" in fieldsets[1][1]["fields"]


class TestProjectAdminViewAsProjectMember(BaseTestCases.BaseTestProjectAdmin):
    def setUp(self):
        super().setUp()

        self.project_member = get_user_model().objects.create_user(
            email="project_participant_user@test.com",
            password="project_participant_user",
            is_staff=True,
        )
        self.change_project.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        self.change_project.participation_set.create(user=self.project_member)
        self.client.force_login(self.project_member)
        self.change_request.user = self.project_member

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
            data={"name": "some project name", "has_accepted_cgu": 1},
        )
        project = Project.objects.get(name="some project name")

        assert response.status_code == 302
        assert project.name == "some project name"
        assert project.leader.user_id == self.project_member.id

    def test_add_project_adds_user_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={"name": "some project name", "has_accepted_cgu": 1},
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_member.id

    @patch("lab.projects.admin.initialize_project_directory")
    def test_add_project_calls_init_directroy_hook(self, init_project_dir_mock):
        request = self.request_factory.post(self.add_view_url)
        request.user = self.project_member
        project = Project(name="Projet Notre Dame")
        ProjectAdmin(Project, admin_site=AdminSite()).save_model(
            request,
            project,
            form=MagicMock(),
            change=False,
        )
        init_project_dir_mock.assert_called_once_with(project.name)

    def test_beamtimerequest_inline_is_present_in_changeview(self):
        inlines = self.project_admin.get_inlines(
            self.change_request, self.change_project
        )
        assert BeamTimeRequestInline in inlines


class TestProjectChangeList(TestCase):
    def test_queryset(self):
        # pylint: disable=expression-not-assigned
        RunFactory(start_date=None).project  # not scheduled project

        scheduled_project = RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=1)
        ).project
        RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=2),
            project=scheduled_project,
        )  # later run to test first_run_date

        project_admin = ProjectAdmin(model=Project, admin_site=AdminSite())
        request = RequestFactory().get(reverse("admin:lab_project_changelist"))
        request.user = LabAdminUserFactory()

        cl = project_admin.get_changelist_instance(request)
        qs = cl.get_queryset(request)

        assert isinstance(cl, ProjectChangeList)
        assert qs.count() == 1
        result = qs.first()
        assert result == scheduled_project
        assert hasattr(result, "first_run_date")
        assert hasattr(result, "number_of_runs")

    def test_projects_with_one_date_is_included(self):
        scheduled_project = RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=1)
        ).project
        RunFactory(start_date=None, end_date=None, project=scheduled_project)

        project_admin = ProjectAdmin(model=Project, admin_site=AdminSite())
        request = RequestFactory().get(reverse("admin:lab_project_changelist"))
        request.user = LabAdminUserFactory()

        cl = project_admin.get_changelist_instance(request)
        qs = cl.get_queryset(request)

        assert qs.filter(id=scheduled_project.id).exists()


class TestProjectDisplayMixin(TestCase):
    def setUp(self):
        self.project = ProjectWithLeaderFactory()
        self.admin = ProjectAdmin(model=Project, admin_site=AdminSite())

    def test_display_first_run_date(self):
        run = RunFactory(
            project=self.project, start_date=timezone.now() + timezone.timedelta(days=1)
        )
        assert self.admin.first_run_date(self.project) == run.start_date

    def test_display_leader_user(self):
        assert self.admin.leader_user(self.project) == self.project.leader.user
        assert self.admin.leader_user(ProjectFactory()) is None

    def test_number_of_runs(self):
        RunFactory(project=self.project)
        RunFactory(project=self.project)
        assert self.admin.number_of_runs(self.project) == 2

    def test_first_run_date_with_link(self):
        run_date = timezone.now() + timezone.timedelta(days=1)
        project_with_scheduled_run = RunFactory(
            project=self.project, start_date=run_date
        ).project
        project_without_scheduled_run = ProjectFactory()

        assert self.admin.first_run_date_with_link(
            project_with_scheduled_run
        ) == date_format(run_date, format="SHORT_DATE_FORMAT", use_l10n=True)
        assert self.admin.first_run_date_with_link(
            project_without_scheduled_run
        ) == '%s <a href="/lab/run/?project=%s" class="fr-link fr-link--sm">%s</a>' % (
            _("No scheduled run."),
            project_without_scheduled_run.id,
            _("See runs"),
        )


class TestProjectAdminChangelistView(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = LabAdminUserFactory()
        self.admin = ProjectAdmin(model=Project, admin_site=AdminSite())
        self.request = RequestFactory().get(reverse("admin:lab_project_changelist"))
        self.request.user = self.admin_user

    def test_has_to_schedule_projects_in_ctx(self):
        pids = [r.project_id for r in RunFactory.create_batch(3, start_date=None)]

        cl_view: TemplateResponse = self.admin.changelist_view(self.request)
        assert "extra_qs" in cl_view.context_data
        assert len(cl_view.context_data["extra_qs"]) == 1
        assert cl_view.context_data["extra_qs"][0]["title"] == _("To schedule")
        qs = cl_view.context_data["extra_qs"][0]["qs"]
        assert qs.count() == 3
        self.assertListEqual(
            list(qs.values_list("id", flat=True)),
            list(reversed(pids)),  # reversed because of ordering
        )
        # test annotation
        first_project = qs.first()
        assert hasattr(first_project, "number_of_runs")
        assert hasattr(first_project, "first_run_date")

    def test_no_to_schedule_projects_in_ctx_when_paginated_results(self):
        for url_query_hiding_qs in ("?q=test", "?p=2", "?status=SCHEDULED"):
            request = RequestFactory().get(
                reverse("admin:lab_project_changelist") + url_query_hiding_qs
            )
            request.user = self.admin_user
            cl_view: TemplateResponse = self.admin.changelist_view(request)
            assert "extra_qs" in cl_view.context_data
            assert (
                len(cl_view.context_data["extra_qs"]) == 0
            ), f"Test failed for query {url_query_hiding_qs}"
