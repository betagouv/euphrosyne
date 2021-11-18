from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ...admin import AnalysisTechniqueUsedAdmin
from ...models import AnalysisTechniqueUsed
from ..factories import RunFactory, StaffUserFactory


class TestAnalysisTechniqueUsedAdminViewAsMember(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.staff_user = StaffUserFactory()
        self.other_run = RunFactory()

    def test_add_run_of_non_lead_project_not_allowed(self):
        "Test add AnalysisTechniqueUsed of non-member Project not allowed"
        request = self.request_factory.get(
            reverse("admin:lab_analysistechniqueused_add")
        )
        request.user = self.staff_user
        admin = AnalysisTechniqueUsedAdmin(
            AnalysisTechniqueUsed, admin_site=AdminSite()
        )
        admin_form = admin.get_form(request, obj=None, change=False)

        form = admin_form(data={"run": self.other_run.id})
        assert len(form.errors["run"]) == 1
        assert (
            "Ce choix ne fait pas partie de ceux disponibles." in form.errors["run"][0]
        )
