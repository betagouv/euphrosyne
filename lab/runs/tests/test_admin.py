from unittest.mock import MagicMock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from data_management.models import LifecycleState, ProjectData
from euphro_auth.tests import factories as auth_factories
from lab.tests import factories

from .. import forms
from ..admin import RunAdmin
from ..models import Run


class TestRunAdminPermissions(TestCase):
    def setUp(self):
        self.run_admin = RunAdmin(model=Run, admin_site=AdminSite())
        self.project = factories.ProjectWithLeaderFactory()
        self.lab_admin = auth_factories.LabAdminUserFactory()
        self.member = get_user_model().objects.get(participation__project=self.project)
        self.new_run = factories.RunFactory(
            status=Run.Status.CREATED, project=self.project
        )
        self.ask_run = factories.RunFactory(
            status=Run.Status.ASK_FOR_EXECUTION, project=self.project
        )

    def test_change_is_allowed_if_new(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.new_run.id])
        )
        request.user = self.member
        assert self.run_admin.has_change_permission(request, self.new_run)

    def test_delete_is_allowed_if_and_admin(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_delete", args=[self.ask_run.id])
        )
        request.user = self.lab_admin
        assert self.run_admin.has_delete_permission(request, self.ask_run)

    def test_delete_is_disallowed_if_member(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_delete", args=[self.new_run.id])
        )
        request.user = self.member
        assert not self.run_admin.has_delete_permission(request, self.new_run)

    def test_change_is_disallowed_if_ask(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.new_run.id])
        )
        request.user = self.member
        assert not self.run_admin.has_change_permission(request, self.ask_run)

    def test_module_is_disallowed(self):
        request = RequestFactory().get("/admin")
        request.user = self.member
        assert not self.run_admin.has_module_permission(request)


class TestRunAdminParams(TestCase):
    def setUp(self):
        self.add_url = reverse("admin:lab_run_add")
        self.run_admin = RunAdmin(model=Run, admin_site=AdminSite())
        self.project = factories.ProjectWithLeaderFactory()
        self.leader_user = self.project.leader.user
        self.member_user = auth_factories.StaffUserFactory()
        self.project.members.add(self.member_user)
        self.lab_admin_user = auth_factories.LabAdminUserFactory()
        self.run = factories.RunFactory(project=self.project)

    def test_project_is_readonly_when_change(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.lab_admin_user
        form = self.run_admin.get_form(request, obj=self.run, change=True)
        assert "project" not in form().fields

    def test_get_form_when_create(self):
        request = RequestFactory().get(reverse("admin:lab_run_add"))

        request.user = self.leader_user
        assert isinstance(
            self.run_admin.get_form(request, obj=None, change=False)(),
            forms.RunCreateForm,
        )

    def test_get_form_when_change(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )

        request.user = self.leader_user
        assert isinstance(
            self.run_admin.get_form(request, obj=None, change=False)(),
            forms.RunCreateForm,
        )

    def test_get_queryset_exludes_non_member_projects(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.leader_user
        other_run = factories.RunFactory()
        assert other_run not in self.run_admin.get_queryset(request)

    def test_formfield_for_foreignkey_restricts_to_member_projects(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.member_user
        other_run = factories.RunFactory()

        project_field_choices = self.run_admin.formfield_for_foreignkey(
            Run._meta.get_field("project"), request
        ).choices
        project_field_choices_names = [choices[1] for choices in project_field_choices]
        assert self.project.name in project_field_choices_names
        assert other_run.project.name not in project_field_choices_names

    def test_get_project_when_editing(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.member_user
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request, self.run.id) == self.run.project

    def test_project_when_adding_from_project(self):
        project = factories.ProjectFactory()
        request = RequestFactory().get(f"{self.add_url}?project={project.id}")
        user = request.user = auth_factories.LabAdminUserFactory()
        project.members.add(user)
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) == project

    def test_project_is_none_when_adding(self):
        request = RequestFactory().get(reverse("admin:lab_run_add"))
        request.user = auth_factories.LabAdminUserFactory()
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) is None

    def test_project_is_none_when_not_a_member(self):
        project = factories.ProjectFactory()
        request = RequestFactory().get(f"{self.add_url}?project={project.id}")
        request.user = auth_factories.StaffUserFactory()
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) is None

    def test_project_when_admin(self):
        project = factories.ProjectFactory()
        request = RequestFactory().get(f"{self.add_url}?project={project.id}")
        request.user = auth_factories.LabAdminUserFactory()
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) == project

    def test_label_is_readonly_when_project_is_immutable(self):
        project_data = ProjectData.for_project(self.run.project)
        project_data.lifecycle_state = LifecycleState.COOL
        project_data.save(update_fields=["lifecycle_state"])
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.lab_admin_user

        assert "label" in self.run_admin.get_readonly_fields(request, self.run)


class TestRunAdminViewAsLeader(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.staff_user = auth_factories.StaffUserFactory()
        self.project_leader_user = auth_factories.StaffUserFactory()
        self.project = factories.ProjectFactory()
        self.project.participation_set.create(
            user=self.project_leader_user, is_leader=True
        )

    @patch("lab.runs.admin.initialize_run_directory")
    def test_add_run_calls_init_directroy_hook(self, init_run_dir_mock):
        request = self.request_factory.post(reverse("admin:lab_run_add"))
        request.user = self.staff_user
        run = Run(label="Run 1")
        run.project = factories.ProjectFactory(name="Le projet du Run 1")
        with patch.object(run, "save"):
            RunAdmin(Run, admin_site=AdminSite()).save_model(
                request,
                run,
                form=MagicMock(),
                change=False,
            )
        init_run_dir_mock.assert_called_once_with(run.project.name, run.label)

    @patch("lab.runs.admin.initialize_run_directory")
    def test_create_run_is_forbidden_when_project_is_cooling(
        self, init_run_dir_mock: MagicMock
    ):
        project_data = ProjectData.for_project(self.project)
        project_data.lifecycle_state = LifecycleState.COOLING
        project_data.save(update_fields=["lifecycle_state"])

        self.client.force_login(self.project_leader_user)
        response = self.client.post(
            reverse("admin:lab_run_add") + f"?project={self.project.id}",
            data={"label": "Run 1"},
        )

        assert response.status_code == 403
        assert not Run.objects.filter(project=self.project, label="Run 1").exists()
        init_run_dir_mock.assert_not_called()

    def test_change_list_view_with_project_lookup_when_project_member(self):
        """Calling changelist_view with a project member should return ok"""
        request = self.request_factory.get(
            reverse("admin:lab_run_changelist") + f"?project={self.project.id}"
        )
        request.user = self.project_leader_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        assert admin.changelist_view(request)

    def test_change_list_view_with_project_lookup_when_not_project_member(self):
        """Calling changelist_view with a non-project member should return 403"""
        request = self.request_factory.get(
            reverse("admin:lab_run_changelist") + f"?project={self.project.id}"
        )
        request.user = self.staff_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        with pytest.raises(PermissionDenied):
            admin.changelist_view(request)

    @patch.object(RunAdmin, "message_user", MagicMock())
    def test_add_redirect_when_no_project_membership(self):
        """Calling add_view with a non-project member should redirect"""
        request = self.request_factory.post(
            reverse("admin:lab_run_add") + f"?project={self.project.id}",
            data={
                "label": "Run 1",
            },
        )
        request.user = self.staff_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        response = admin.changeform_view(request, None)

        assert response.status_code == 302

    def test_run_creation_button_is_disabled_when_project_is_immutable(self):
        project_data = ProjectData.for_project(self.project)
        project_data.lifecycle_state = LifecycleState.COOLING
        project_data.save(update_fields=["lifecycle_state"])
        self.client.force_login(self.project_leader_user)

        response = self.client.get(
            reverse("admin:lab_run_changelist") + f"?project={self.project.id}"
        )
        html = response.content.decode()

        assert response.status_code == 200
        assert 'type="button" disabled' in html
        assert (
            reverse("admin:lab_run_add") + f"?project={self.project.id}"
        ) not in html

    def test_run_creation_button_is_disabled_when_project_is_immutable_with_runs(self):
        run = factories.RunFactory(project=self.project)
        project_data = ProjectData.for_project(self.project)
        project_data.lifecycle_state = LifecycleState.COOLING
        project_data.save(update_fields=["lifecycle_state"])
        self.client.force_login(self.project_leader_user)

        response = self.client.get(
            reverse("admin:lab_run_changelist") + f"?project={self.project.id}"
        )
        html = response.content.decode()

        assert response.status_code == 200
        assert run.label in html
        assert 'type="button" disabled' in html
        assert (
            reverse("admin:lab_run_add") + f"?project={self.project.id}"
        ) not in html

    @patch("django.middleware.csrf.CsrfViewMiddleware._check_token", lambda *args: None)
    def test_changing_run(self):
        run = factories.RunFactory(label="Run 1", project=self.project)
        data = {
            "particle_type": "Proton",
            "energy_in_keV_Proton": "1000",
            "energy_in_keV_Alpha+particle": "",
            "energy_in_keV_Deuton": "",
            "beamline": "Microbeam",
            "method_PIXE": "on",
            "detector_LE0": "on",
            "filters_for_detector_LE0": "Helium",
            "filters_for_detector_HE1": "",
            "filters_for_detector_HE2": "",
            "filters_for_detector_HE3": "",
            "filters_for_detector_HE4": "",
            "detector_IBIL_other": "",
            "detector_FORS_other": "",
            "detector_ERDA": "",
            "detector_NRA": "",
        }

        self.client.force_login(self.project_leader_user)
        self.client.post(
            reverse("admin:lab_run_change", args=[run.id]),
            data=data,
        )

        run = Run.objects.get(pk=run.id)
        assert run.particle_type == "Proton"
        assert run.energy_in_keV == 1000
        assert run.beamline == "Microbeam"
        assert run.method_PIXE
        assert run.detector_LE0
        assert run.filters_for_detector_LE0 == "Helium"
        assert not run.filters_for_detector_HE1


class TestRunAdminViewAsAdmin(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin_user = auth_factories.LabAdminUserFactory()
        self.admin_project_1 = factories.ProjectFactory()
        self.admin_project_1.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        self.project_1_run_1 = factories.RunFactory(project=self.admin_project_1)
        self.admin_project_2 = factories.ProjectFactory()
        self.admin_project_2.participation_set.create(
            user=self.admin_user, is_leader=True
        )

    def test_change_project_of_run_is_ignored(self):
        "Test change run project is ignored thanks to excluding project field"
        request = self.request_factory.post(
            reverse(
                "admin:lab_run_change",
                args=[self.project_1_run_1.id],
            )
        )
        request.user = self.admin_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        admin_form = admin.get_form(request, obj=self.project_1_run_1, change=True)

        form = admin_form(
            data={
                "label": "dummy",
                "project": self.admin_project_2.id,
                "beamline": "Microbeam",
            }
        )
        assert "project" not in form.fields

    def test_change_list_view_with_project_lookup_when_admin(self):
        """Calling changelist_view with an admin should return ok"""
        project = factories.ProjectFactory()
        request = self.request_factory.get(
            reverse("admin:lab_run_changelist") + f"?project={project.id}"
        )
        request.user = self.admin_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        assert admin.changelist_view(request)

    @patch("lab.runs.admin.rename_run_directory")
    def test_change_run_label_calls_hook(self, rename_run_dir_mock):
        run = factories.RunFactory()
        request = self.request_factory.post(
            reverse(
                "admin:lab_run_change",
                args=[run.id],
            ),
            data={
                "label": "new-run-name",
                "particle_type": "",
                "energy_in_keV_Proton": "",
                "energy_in_keV_Alpha particle": "",
                "energy_in_keV_Deuton": "",
                "beamline": "Microbeam",
                "filters_for_detector_LE0": "",
                "filters_for_detector_HE1": "",
                "filters_for_detector_HE2": "",
                "filters_for_detector_HE3": "",
                "filters_for_detector_HE4": "",
                "detector_IBIL_other": "",
                "detector_FORS_other": "",
                "detector_ERDA": "",
                "detector_NRA": "",
                "Run_run_object_groups-TOTAL_FORMS": "0",
                "Run_run_object_groups-INITIAL_FORMS": "0",
            },
        )
        request.user = self.admin_user
        with patch.object(run, "save"):
            run_admin = RunAdmin(Run, admin_site=AdminSite())
            form_class = run_admin.get_form(request, obj=run, change=True)
            form = form_class(request.POST, request.FILES, instance=run)
            # Clean form to populate run instance
            assert form.is_valid()
            run_admin.save_model(request, run, form=form, change=True)
        rename_run_dir_mock.assert_called_once_with(
            run.project.name, form.initial["label"], "new-run-name"
        )

    @patch("lab.runs.admin.rename_run_directory")
    def test_change_run_label_is_forbidden_when_project_is_cool(
        self, rename_run_dir_mock: MagicMock
    ):
        run = factories.RunFactory()
        project_data = ProjectData.for_project(run.project)
        project_data.lifecycle_state = LifecycleState.COOL
        project_data.save(update_fields=["lifecycle_state"])
        request = self.request_factory.post(
            reverse("admin:lab_run_change", args=[run.id]),
            data={
                "label": "new-run-name",
                "particle_type": "",
                "energy_in_keV_Proton": "",
                "energy_in_keV_Alpha particle": "",
                "energy_in_keV_Deuton": "",
                "beamline": "Microbeam",
                "filters_for_detector_LE0": "",
                "filters_for_detector_HE1": "",
                "filters_for_detector_HE2": "",
                "filters_for_detector_HE3": "",
                "filters_for_detector_HE4": "",
                "detector_IBIL_other": "",
                "detector_FORS_other": "",
                "detector_ERDA": "",
                "detector_NRA": "",
                "Run_run_object_groups-TOTAL_FORMS": "0",
                "Run_run_object_groups-INITIAL_FORMS": "0",
            },
        )
        request.user = self.admin_user
        run_admin = RunAdmin(Run, admin_site=AdminSite())
        form_class = run_admin.get_form(request, obj=run, change=True)
        form = form_class(request.POST, request.FILES, instance=run)
        assert form.is_valid()

        with pytest.raises(PermissionDenied):
            run_admin.save_model(request, run, form=form, change=True)

        rename_run_dir_mock.assert_not_called()


class TestRunAdminMethodFieldset(TestCase):
    def setUp(self):
        self.project = factories.ProjectFactory()
        self.run = factories.RunFactory(project=self.project)
        self.request = RequestFactory().get(
            reverse(
                "admin:lab_run_change",
                args=[self.run.id],
            )
            + f"?project={self.project.id}"
        )
        self.admin_user = auth_factories.LabAdminUserFactory()
        self.request.user = self.admin_user
        self.request.resolver_match = MagicMock()
        self.run_admin = RunAdmin(Run, admin_site=AdminSite())
        self.admin_form = self.run_admin.get_form(self.request, obj=None, change=False)

    def test_methods_fieldset_is_defined(self):
        assert "METHODS" in [
            fieldset_name
            for fieldset_name, fieldset_options in self.run_admin.get_fieldsets(
                self.request, self.run
            )
        ]

    def test_methods_fieldset_is_rendered(self):
        resp = self.run_admin.change_view(self.request, str(self.run.id))
        resp.render()
        assert '<fieldset id="METHODS"' in resp.content.decode()


# pylint: disable=too-many-instance-attributes
class TestRunAdminScheduleAction(TestCase):
    def setUp(self):
        self.run = factories.RunFactory()
        self.project = self.run.project
        self.admin_user = auth_factories.LabAdminUserFactory()
        self.run_admin = RunAdmin(Run, admin_site=AdminSite())

        now = timezone.now()
        self.start_date = now + timezone.timedelta(days=14)
        self.end_date = now + timezone.timedelta(days=15)
        self.embargo_date = now + timezone.timedelta(days=365 * 2)
        self.correct_data = {
            "_action": "schedule_run",
            "_continue": "1",
            "start_date_0": self.start_date.date().strftime("%Y-%m-%d"),
            "start_date_1": self.start_date.time().strftime("%H:%M:%S"),
            "end_date_0": self.end_date.date().strftime("%Y-%m-%d"),
            "end_date_1": self.end_date.time().strftime("%H:%M:%S"),
            "embargo_date": self.embargo_date.date().strftime("%Y-%m-%d"),
        }

    def test_schedule_form_is_rendered(self):
        request = RequestFactory().get(
            reverse(
                "admin:lab_run_change",
                args=[self.run.id],
            )
            + f"?project={self.project.id}"
        )
        request.user = self.admin_user
        request.resolver_match = MagicMock()

        resp = self.run_admin.change_view(request, str(self.run.id))
        resp.render()

        assert "schedule_modal" in resp.context_data
        assert resp.context_data["schedule_modal"]["id"] == "schedule-modal"
        assert isinstance(
            resp.context_data["schedule_modal"]["form"], forms.RunScheduleForm
        )
        assert '<form id="schedule-modal-form"' in resp.content.decode()

    def test_schedule_action_as_admin(self):
        request = RequestFactory().post(
            reverse(
                "admin:lab_run_change",
                args=[self.run.id],
            ),
            data=self.correct_data,
        )
        request.user = self.admin_user

        with timezone.override("UTC"):
            response = self.run_admin.changeform_view(request, str(self.run.id))

        run = Run.objects.get(pk=self.run.id)
        assert response.status_code == 200
        assert self.start_date.strftime("%Y-%m-%d %H:%M:%S") == run.start_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        assert self.end_date.strftime("%Y-%m-%d %H:%M:%S") == run.end_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        assert self.embargo_date.strftime("%Y-%m-%d") == run.embargo_date.strftime(
            "%Y-%m-%d"
        )

    def test_schedule_action_as_non_admin(self):
        request = RequestFactory().post(
            reverse(
                "admin:lab_run_change",
                args=[self.run.id],
            ),
            data=self.correct_data,
        )
        request.user = auth_factories.StaffUserFactory()
        self.run.project.members.add(request.user)

        with pytest.raises(PermissionDenied):
            self.run_admin.changeform_view(request, str(self.run.id))

    def test_schedule_action_is_forbidden_when_project_is_cool(self):
        project_data = ProjectData.for_project(self.project)
        project_data.lifecycle_state = LifecycleState.COOL
        project_data.save(update_fields=["lifecycle_state"])
        old_start_date = self.run.start_date
        old_end_date = self.run.end_date

        request = RequestFactory().post(
            reverse("admin:lab_run_change", args=[self.run.id]),
            data=self.correct_data,
        )
        request.user = self.admin_user

        with pytest.raises(PermissionDenied):
            self.run_admin.changeform_view(request, str(self.run.id))

        self.run.refresh_from_db()
        assert self.run.start_date == old_start_date
        assert self.run.end_date == old_end_date
