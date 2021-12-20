from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ...documents.api_views import presigned_document_upload_url_view
from ..factories import LabAdminUserFactory, ProjectWithLeaderFactory, StaffUserFactory


class TestPresignedDocumentUploadUrlView(TestCase):
    def setUp(self):
        self.project = ProjectWithLeaderFactory()

    def test_admins_can_view(self):
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[self.project.id])
        )
        request.user = LabAdminUserFactory()
        response = presigned_document_upload_url_view(request, self.project.id)
        assert response.status_code == 200
        assert b"url" in response.content

    def test_members_can_view(self):
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[self.project.id])
        )
        request.user = self.project.leader.user
        response = presigned_document_upload_url_view(request, self.project.id)
        assert response.status_code == 200
        assert b"url" in response.content

    def test_staff_users_are_forbidden(self):
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[self.project.id])
        )
        request.user = StaffUserFactory()
        with self.assertRaises(PermissionDenied):
            presigned_document_upload_url_view(request, self.project.id)
