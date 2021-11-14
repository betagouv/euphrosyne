from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from ...admin import RunAdmin
from ...models import Project, Run


class TestRunAdminViewAsLeader(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.project_leader_user = get_user_model().objects.create_user(
            email="leader_user@test.com", password="leader_user", is_staff=True
        )
        self.project_leader_user_2 = get_user_model().objects.create_user(
            email="leader_user_2@test.com", password="leader_user_2", is_staff=True
        )
        self.existing_project_2 = Project.objects.create(name="some project name 2")
        self.existing_project_2.participation_set.create(
            user=self.project_leader_user_2, is_leader=True
        )

    def test_add_run_of_non_lead_project_not_allowed(self):
        "Test add Run of non-lead Project not allowed via formfield_for_foreignkey"
        request = self.request_factory.get(reverse("admin:lab_run_add"))
        request.user = self.project_leader_user
        admin = RunAdmin(Run, admin_site=AdminSite())
        admin_form = admin.get_form(request, obj=None, change=False)

        form = admin_form(data={"project": self.existing_project_2.id})
        assert len(form.errors["project"]) == 1
        assert (
            "Ce choix ne fait pas partie de ceux disponibles."
            in form.errors["project"][0]
        )


class TestRunAdminViewAsAdmin(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin_user = get_user_model().objects.create_user(
            email="admin_user@test.com",
            password="admin_user",
            is_staff=True,
            is_lab_admin=True,
        )
        self.admin_project_1 = Project.objects.create(name="some project name")
        self.admin_project_1.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        self.project_1_run_1 = Run.objects.create(
            label="run 1", project=self.admin_project_1
        )
        self.admin_project_2 = Project.objects.create(name="some other project name")
        self.admin_project_2.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        self.client.force_login(self.admin_user)

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
