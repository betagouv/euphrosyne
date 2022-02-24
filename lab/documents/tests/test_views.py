from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ...documents.views import ProjectDocumentsView
from ...tests.factories import (
    LabAdminUserFactory,
    ProjectWithLeaderFactory,
    StaffUserFactory,
)


class TestProjectDocumentsView(TestCase):
    def setUp(self):
        self.project = ProjectWithLeaderFactory()

    def test_admins_can_view(self):
        request = RequestFactory().get(
            reverse("admin:lab_project_documents", args=[self.project.id])
        )
        request.user = LabAdminUserFactory()
        view = ProjectDocumentsView()
        view.request = request
        view.dispatch(
            request,
            project_id=self.project.id,
        )

    def test_members_can_view(self):
        request = RequestFactory().get(
            reverse("admin:lab_project_documents", args=[self.project.id])
        )
        request.user = self.project.leader.user
        view = ProjectDocumentsView()
        view.request = request
        view.dispatch(request, self.project.id)

    def test_staff_users_are_forbidden(self):
        request = RequestFactory().get(
            reverse("admin:lab_project_documents", args=[self.project.id])
        )
        request.user = StaffUserFactory()
        view = ProjectDocumentsView()
        view.request = request
        with self.assertRaises(PermissionDenied):
            view.dispatch(request, self.project.id)
