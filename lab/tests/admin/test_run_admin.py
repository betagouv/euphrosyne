from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from ...admin import RunAdmin
from ...models import Run
from .. import factories


class TestRunAdminPermissions(TestCase):
    def setUp(self):
        self.run_admin = RunAdmin(model=Run, admin_site=AdminSite())
        self.project = factories.ProjectWithLeaderFactory()
        self.member = get_user_model().objects.get(participation__project=self.project)
        self.new_run = factories.RunFactory(status=Run.Status.NEW, project=self.project)
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
        self.leader_user = get_user_model().objects.get(
            participation__project=self.project, participation__is_leader=True
        )
        self.lab_admin_user = factories.LabAdminUserFactory()
        self.run = factories.RunFactory(project=self.project)

    def test_project_is_readonly_when_change(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.lab_admin_user
        assert "project" in self.run_admin.get_readonly_fields(request, self.run)

    def test_dates_are_readonly_when_change_as_leader(self):
        request = RequestFactory().get(
            reverse("admin:lab_run_change", args=[self.run.id])
        )
        request.user = self.leader_user
        assert "start_date" in self.run_admin.get_readonly_fields(request, self.run)
        assert "end_date" in self.run_admin.get_readonly_fields(request, self.run)

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
        request.user = self.leader_user
        other_run = factories.RunFactory()
        assert (
            other_run.project
            not in self.run_admin.formfield_for_foreignkey(
                Run._meta.get_field("project"), request
            ).choices
        )


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
                "beamline": list(Run.BEAMLINE_NAMES.keys())[0],
            }
        )
        assert "project" not in form.fields
