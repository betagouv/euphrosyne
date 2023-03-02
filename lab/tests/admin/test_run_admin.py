from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from lab.models.project import Project

from ...admin import RunAdmin
from ...models import Run
from .. import factories


class TestRunAdminPermissions(TestCase):
    def setUp(self):
        self.run_admin = RunAdmin(model=Run, admin_site=AdminSite())
        self.project = factories.ProjectWithLeaderFactory()
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

    def test_delete_is_allowed_if_new(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_delete", args=[self.new_run.id])
        )
        request.user = self.member
        assert self.run_admin.has_delete_permission(request, self.new_run)

    def test_change_is_disallowed_if_ask(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.new_run.id])
        )
        request.user = self.member
        assert not self.run_admin.has_change_permission(request, self.ask_run)

    def test_delete_is_disallowed_if_ask(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_delete", args=[self.new_run.id])
        )
        request.user = self.member
        assert not self.run_admin.has_delete_permission(request, self.ask_run)

    def test_module_is_disallowed(self):
        request = RequestFactory().get("/admin")
        request.user = self.member
        assert not self.run_admin.has_module_permission(request)


class TestRunAdminParams(TestCase):
    def setUp(self):
        self.run_admin = RunAdmin(model=Run, admin_site=AdminSite())
        self.project = factories.ProjectWithLeaderFactory()
        self.leader_user = self.project.leader.user
        self.member_user = factories.StaffUserFactory()
        self.project.members.add(self.member_user)
        self.lab_admin_user = factories.LabAdminUserFactory()
        self.run = factories.RunFactory(project=self.project)

    def test_project_is_readonly_when_change(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.lab_admin_user
        assert "project" in self.run_admin.get_readonly_fields(request, self.run)

    def test_dates_are_readonly_when_change_as_non_admin(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.leader_user
        assert "start_date" in self.run_admin.get_readonly_fields(request, self.run)
        assert "end_date" in self.run_admin.get_readonly_fields(request, self.run)

        request.user = self.lab_admin_user
        assert "start_date" not in self.run_admin.get_readonly_fields(request, self.run)
        assert "end_date" not in self.run_admin.get_readonly_fields(request, self.run)

    def test_dates_are_readonly_when_add_as_non_admin(self):
        request = RequestFactory().get(reverse("admin:lab_run_add"))

        request.user = self.leader_user
        assert "start_date" in self.run_admin.get_readonly_fields(request)
        assert "end_date" in self.run_admin.get_readonly_fields(request)

        request.user = self.lab_admin_user
        assert "start_date" not in self.run_admin.get_readonly_fields(request)
        assert "end_date" not in self.run_admin.get_readonly_fields(request)

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
        add_url = reverse("admin:lab_run_add")
        request = RequestFactory().get(f"{add_url}?project={project.id}")
        request.user = factories.StaffUserFactory()
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) == project

    def test_project_is_none_when_adding(self):
        request = RequestFactory().get(reverse("admin:lab_run_add"))
        request.user = factories.StaffUserFactory()
        # pylint: disable=protected-access
        assert self.run_admin._get_project(request) is None


class TestRunAdminViewAsLeader(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.staff_user = factories.StaffUserFactory()
        self.project_leader_user = factories.StaffUserFactory()
        self.project = factories.ProjectFactory()
        self.project.participation_set.create(
            user=self.project_leader_user, is_leader=True
        )

    def test_add_run_of_non_lead_project_not_allowed(self):
        "Test add Run of non-lead Project not allowed via formfield_for_foreignkey"
        request = self.request_factory.get(reverse("admin:lab_run_add"))
        request.user = self.staff_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        admin_form = admin.get_form(request, obj=None, change=False)

        form = admin_form(data={"project": self.project.id})
        assert len(form.errors["project"]) == 1
        assert (
            "Ce choix ne fait pas partie de ceux disponibles."
            in form.errors["project"][0]
        )

    @patch("lab.admin.run.initialize_run_directory")
    def test_add_run_calls_init_directroy_hook(self, init_run_dir_mock):
        request = self.request_factory.post(reverse("admin:lab_run_add"))
        request.user = self.staff_user
        run = Run(label="Run 1")
        run.project = Project(name="Le projet du Run 1")
        with patch.object(run, "save"):
            RunAdmin(Run, admin_site=AdminSite()).save_model(
                request,
                run,
                form=MagicMock(),
                change=False,
            )
        init_run_dir_mock.assert_called_once_with(run.project.name, run.label)

    @patch("lab.admin.run.rename_run_directory")
    def test_change_run_label_calls_hook(self, rename_run_dir_mock):
        run = factories.RunFactory()
        run.project.members.add(self.staff_user)
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
        request.user = self.staff_user
        with patch.object(run, "save"):
            run_admin = RunAdmin(Run, admin_site=AdminSite())
            form_class = run_admin.get_form(request, obj=run, change=True)
            form = form_class(request.POST, request.FILES, instance=run)
            # Clean form to populate run instance
            form.is_valid()
            run_admin.save_model(request, run, form=form, change=True)
        rename_run_dir_mock.assert_called_once_with(
            run.project.name, form.initial["label"], "new-run-name"
        )


class TestRunAdminViewAsAdmin(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin_user = factories.LabAdminUserFactory()
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


class TestRunAdminMethodFieldset(TestCase):
    def setUp(self):
        self.request = RequestFactory().get(
            reverse(
                "admin:lab_run_add",
            )
        )
        self.admin_user = factories.LabAdminUserFactory()
        self.request.user = self.admin_user
        self.run_admin = RunAdmin(Run, admin_site=AdminSite())
        self.admin_form = self.run_admin.get_form(self.request, obj=None, change=False)

    def test_methods_fieldset_is_defined(self):
        assert "METHODS" in [
            fieldset_name
            for fieldset_name, fieldset_options in self.run_admin.get_fieldsets(
                self.request
            )
        ]

    def test_methods_fieldset_is_rendered(self):
        resp = self.run_admin.add_view(self.request)
        resp.render()
        assert '<fieldset id="METHODS"' in resp.content.decode()
