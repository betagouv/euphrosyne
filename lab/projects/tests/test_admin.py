from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from data_management.models import LifecycleState, ProjectData
from euphro_auth.tests.factories import LabAdminUserFactory
from lab.models import Institution
from lab.tests.factories import (
    EmployerFactory,
    InstitutionFactory,
    ParticipationFactory,
    ProjectFactory,
    ProjectWithLeaderFactory,
    RunFactory,
)

from ..admin import ProjectAdmin, ProjectChangeList
from ..admin_filters import ProjectStatusListFilter
from ..inlines import (
    BeamTimeRequestInline,
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
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.confidential is True

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

    def test_name_is_readonly_for_admin_when_project_is_immutable(self):
        project_data = ProjectData.for_project(self.change_project)
        project_data.lifecycle_state = LifecycleState.COOL
        project_data.save(update_fields=["lifecycle_state"])

        assert "name" in self.project_admin.get_readonly_fields(
            self.change_request, self.change_project
        )

    @patch("lab.projects.admin.rename_project_directory")
    def test_change_project_name_calls_hook(self, rename_project_dir_mock):
        project = ProjectFactory(name="project a")
        request = self.request_factory.post(
            reverse("admin:lab_project_change", args=[project.id]),
            data={
                "name": "project b",
            },
        )
        request.user = self.admin_user
        with patch.object(project, "save"):
            project_admin = ProjectAdmin(Project, admin_site=AdminSite())
            form_class = project_admin.get_form(request, obj=project, change=True)
            form = form_class(request.POST, request.FILES, instance=project)
            # Clean form to populate run instance
            assert form.is_valid()
            project_admin.save_model(request, project, form=form, change=True)
        rename_project_dir_mock.assert_called_once_with("project a", "project b")

    @patch("lab.projects.admin.rename_project_directory")
    def test_change_project_name_is_forbidden_when_project_is_cool(
        self, rename_project_dir_mock: MagicMock
    ):
        project = ProjectFactory(name="project a")
        project_data = ProjectData.for_project(project)
        project_data.lifecycle_state = LifecycleState.COOL
        project_data.save(update_fields=["lifecycle_state"])
        request = self.request_factory.post(
            reverse("admin:lab_project_change", args=[project.id]),
            data={
                "name": "project b",
            },
        )
        request.user = self.admin_user
        project_admin = ProjectAdmin(Project, admin_site=AdminSite())
        project.name = "project b"
        form = MagicMock()
        form.changed_data = ["name"]
        form.initial = {"name": "project a"}

        with pytest.raises(PermissionDenied):
            project_admin.save_model(request, project, form=form, change=True)

        rename_project_dir_mock.assert_not_called()


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

    def test_create_project(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
                "institution__name": "Louvre",
                "institution__country": "France",
                "employer_first_name": "John",
                "employer_last_name": "Doe",
                "employer_email": "john.doe@example.com",
                "employer_function": "Manager",
            },
        )
        assert response.status_code == 302
        assert Project.objects.get(name="some project name")

    def test_create_project_should_accept_cgu(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "comments": "some comments",
            },
        )
        assert response.status_code == 200
        assert not Project.objects.filter(name="some project name").exists()

    def test_create_project_should_provide_institution(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
            },
        )
        assert response.status_code == 200
        assert not Project.objects.filter(name="some project name").exists()

    def test_create_project_creates_leader(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
                "institution__name": "C3",
                "institution__country": "France",
                "institution__ror_id": "https://ror.org/123456789",
                "employer_first_name": "John",
                "employer_last_name": "Doe",
                "employer_email": "john.doe@example.com",
                "employer_function": "Manager",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.leader
        assert project.leader.user_id == self.project_leader.id
        assert project.leader.institution.name == "C3"
        assert project.leader.on_premises

    def test_create_project_creates_employer(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
                "institution__name": "C3",
                "institution__country": "France",
                "employer_first_name": "John",
                "employer_last_name": "Doe",
                "employer_email": "john.doe@example.com",
                "employer_function": "Manager",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.leader.employer is not None
        assert project.leader.employer.first_name == "John"
        assert project.leader.employer.last_name == "Doe"
        assert project.leader.employer.email == "john.doe@example.com"
        assert project.leader.employer.function == "Manager"

    def test_create_project_employer_fields_are_required(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
                "institution__name": "C3",
                "institution__country": "France",
            },
        )
        assert response.status_code == 200
        assert not Project.objects.filter(name="some project name").exists()

    def test_add_project_form_prefills_employer_from_last_participation(self):
        """Prefill employer fields with the last participation's employer data."""
        employer = EmployerFactory(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            function="Director",
        )
        ParticipationFactory(
            user=self.project_leader,
            institution=self.base_institution,
            employer=employer,
        )
        response = self.client.get(self.add_view_url)
        content = response.content.decode()
        assert 'value="Jane"' in content
        assert 'value="Smith"' in content
        assert 'value="jane.smith@example.com"' in content
        assert 'value="Director"' in content

    def test_add_project_form_has_employer_fields(self):
        fieldsets = self.project_admin.get_fieldsets(self.add_request)
        employer_fieldset_found = False
        for __, fieldset_data in fieldsets:
            if "employer_first_name" in str(fieldset_data.get("fields", [])):
                employer_fieldset_found = True
                assert "employer_last_name" in str(fieldset_data["fields"])
                assert "employer_email" in str(fieldset_data["fields"])
                assert "employer_function" in str(fieldset_data["fields"])
                break
        assert employer_fieldset_found

    def test_create_project_use_existing_institution(self):
        i, _ = Institution.objects.get_or_create(
            name="C2", country="France", ror_id="https://ror.org/123456789"
        )
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": True,
                "comments": "some comments",
                "institution__name": "C2",
                "institution__country": "France",
                "institution__ror_id": "https://ror.org/123456789",
                "employer_first_name": "John",
                "employer_last_name": "Doe",
                "employer_email": "john.doe@example.com",
                "employer_function": "Manager",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.leader.institution_id == i.id

    def test_change_leader_link_is_hidden(self):
        response = self.client.get(
            reverse("admin:lab_project_change", args=[self.change_project.id])
        )

        assert "change-leader-link" not in response.content.decode()

    def test_name_is_readonly_when_change(self):
        assert "name" in self.project_admin.get_readonly_fields(
            self.change_request, self.change_project
        )

    def test_name_is_not_readonly_when_add(self):
        assert "name" not in self.project_admin.get_readonly_fields(self.add_request)

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
        # Find the fieldset containing has_accepted_cgu
        has_cgu_field = False
        for __, fieldset_data in fieldsets:
            if "has_accepted_cgu" in str(fieldset_data.get("fields", [])):
                has_cgu_field = True
                break
        assert has_cgu_field

    @patch("lab.projects.admin.rename_project_directory")
    def test_change_project_name_not_call_hook(self, rename_project_dir_mock):
        request = self.request_factory.post(
            reverse("admin:lab_project_change", args=[self.change_project.id]),
            data={
                "name": "project b",
            },
        )
        request.user = self.project_leader
        with patch.object(self.change_project, "save"):
            project_admin = ProjectAdmin(Project, admin_site=AdminSite())
            form_class = project_admin.get_form(
                request, obj=self.change_project, change=True
            )
            form = form_class(request.POST, request.FILES, instance=self.change_project)
            # Clean form to populate run instance
            assert form.is_valid()
            project_admin.save_model(
                request, self.change_project, form=form, change=True
            )
        rename_project_dir_mock.assert_not_called()


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

    def test_add_project_comments_is_mandatory(self):
        response = self.client.post(
            self.add_view_url,
            data={"name": "some project name", "has_accepted_cgu": 1, "comments": ""},
        )

        assert Project.objects.filter(name="some project name").first() is None
        assert response.status_code == 200

    def test_add_project_comments_max_length(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": 1,
                "comments": "a" * 561,  # 561 characters
            },
        )

        assert Project.objects.filter(name="some project name").first() is None
        assert response.status_code == 200
        assert "id_comments_error" in response.content.decode()

    def test_add_project_adds_user_as_member(self):
        response = self.client.post(
            self.add_view_url,
            data={
                "name": "some project name",
                "has_accepted_cgu": 1,
                "comments": "some comments",
                "institution__name": "Louvre",
                "institution__country": "France",
                "employer_first_name": "John",
                "employer_last_name": "Doe",
                "employer_email": "john.doe@example.com",
                "employer_function": "Manager",
            },
        )
        assert response.status_code == 302
        project = Project.objects.get(name="some project name")
        assert project.members.count() == 1
        assert project.members.all()[0].id == self.project_member.id

    @patch("lab.projects.admin.initialize_project_directory")
    def test_add_project_calls_init_directroy_hook(self, init_project_dir_mock):
        request = self.request_factory.post(self.add_view_url)
        request.user = self.project_member
        project = MagicMock(name="Projet Notre Dame")
        form = MagicMock()
        form.cleaned_data = {
            "institution": self.base_institution,
            "employer_first_name": "John",
            "employer_last_name": "Doe",
            "employer_email": "john.doe@example.com",
            "employer_function": "Manager",
        }
        ProjectAdmin(Project, admin_site=AdminSite()).save_model(
            request,
            project,
            form=form,
            change=False,
        )
        init_project_dir_mock.assert_called_once_with(project.name)

    def test_add_project_form_prefill_last_institution(self):
        """Prefill institution field with the last used institution."""
        institution = InstitutionFactory()
        ParticipationFactory(user=self.project_member, institution=institution)
        response = self.client.get(self.add_view_url)
        assert f'value="{institution.name}"' in response.content.decode()

    def test_add_project_form_prefill_last_institution_when_no_participaion(self):
        """No prefill when user has no participation."""
        self.project_member.participation_set.all().delete()
        response = self.client.get(self.add_view_url)
        assert response.status_code == HTTPStatus.OK

    def test_beamtimerequest_inline_is_present_in_changeview(self):
        inlines = self.project_admin.get_inlines(
            self.change_request, self.change_project
        )
        assert BeamTimeRequestInline in inlines

    def test_leader_participation_inline_not_present_in_changeview(self):
        """LeaderParticipationInline should no longer be in inlines."""
        inlines = self.project_admin.get_inlines(
            self.change_request, self.change_project
        )
        # Check that no inline class name contains "LeaderParticipation"
        inline_names = [inline.__name__ for inline in inlines]
        assert not any("LeaderParticipation" in name for name in inline_names)


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
        self.status_filter_param = ProjectStatusListFilter.parameter_name

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
        for url_query_hiding_qs in (
            "?q=test",
            "?p=2",
            f"?{self.status_filter_param}=SCHEDULED",
        ):
            request = RequestFactory().get(
                reverse("admin:lab_project_changelist") + url_query_hiding_qs
            )
            request.user = self.admin_user
            cl_view: TemplateResponse = self.admin.changelist_view(request)
            assert "extra_qs" in cl_view.context_data
            assert (
                len(cl_view.context_data["extra_qs"]) == 0
            ), f"Test failed for query {url_query_hiding_qs}"

    def test_scheduled_project_in_to_schedule_qs_when_any_to_schedule_run(self):
        project_both_scheduled_and_not = ProjectFactory()
        RunFactory(project=project_both_scheduled_and_not, start_date=timezone.now())
        RunFactory(project=project_both_scheduled_and_not, start_date=None)

        project_scheduled = ProjectFactory()
        RunFactory(project=project_scheduled, start_date=timezone.now())

        project_not_scheduled = ProjectFactory()
        RunFactory(project=project_not_scheduled, start_date=None)

        cl_view: TemplateResponse = self.admin.changelist_view(self.request)

        to_schedule_qs = cl_view.context_data["extra_qs"][0]["qs"]
        scheduled_qs = cl_view.context_data["cl"].queryset

        assert to_schedule_qs.count() == 2
        assert project_both_scheduled_and_not in to_schedule_qs.all()
        assert project_not_scheduled in to_schedule_qs.all()
        assert scheduled_qs.count() == 2
        assert project_both_scheduled_and_not in scheduled_qs.all()
        assert project_scheduled in scheduled_qs.all()
