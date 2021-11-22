from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from ...models import Project, Run


class TestRunAdminViewAsLeader(TestCase):
    def setUp(self):
        self.client = Client()
        self.project_leader_user = get_user_model().objects.create_user(
            email="leader_user@test.com", password="leader_user", is_staff=True
        )
        self.existing_project = Project.objects.create(name="some project name")
        self.existing_project.participation_set.create(
            user=self.project_leader_user, is_leader=True
        )
        self.project_leader_user_2 = get_user_model().objects.create_user(
            email="leader_user_2@test.com", password="leader_user_2", is_staff=True
        )
        self.existing_project_2 = Project.objects.create(name="some project name 2")
        self.existing_project_2.participation_set.create(
            user=self.project_leader_user_2, is_leader=True
        )
        self.client.force_login(self.project_leader_user)

    def test_add_run_of_non_lead_project_not_allowed(self):
        "Test add Run of non-lead Project not allowed via formfield_for_foreignkey"
        response = self.client.post(
            reverse("admin:lab_run_add"),
            data={
                "label": "new run label",
                "project": self.existing_project_2.id,
                "date_0": timezone.now().date(),
                "date_1": timezone.now().time(),
            },
        )
        assert response.status_code == 200
        assert Run.objects.all().count() == 0
        assert (
            "Ce choix ne fait pas partie de ceux disponibles."
            in response.content.decode()
        )


class TestRunAdminViewAsAdmin(TestCase):
    def setUp(self):
        self.client = Client()
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
            label="run 1", project=self.admin_project_1, date=timezone.now()
        )
        self.admin_project_2 = Project.objects.create(name="some other project name")
        self.admin_project_2.participation_set.create(
            user=self.admin_user, is_leader=True
        )
        self.client.force_login(self.admin_user)

    def test_change_project_of_run_is_ignored(self):
        "Test change run project is ignored thanks to excluding project field"
        response = self.client.post(
            reverse(
                "admin:lab_run_change",
                args=[self.project_1_run_1.id],
            ),
            data={
                "label": self.project_1_run_1.label,
                "project": self.admin_project_2.id,
                "date_0": timezone.now().date(),
                "date_1": timezone.now().time(),
            },
        )
        assert response.status_code == 302
        self.project_1_run_1.refresh_from_db()
        assert self.project_1_run_1.project_id == self.admin_project_1.id
        assert self.project_1_run_1.project_id != self.admin_project_2.id
