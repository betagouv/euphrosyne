from unittest.mock import MagicMock

from django.http.response import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ...documents.api_views import project_membership_required
from ...tests.factories import (
    LabAdminUserFactory,
    ProjectFactory,
    ProjectWithLeaderFactory,
    StaffUserFactory,
)


class TestProjectMembershipRequiredDecorator(TestCase):
    @staticmethod
    def test_admin_user_passes_check():
        project = ProjectFactory()
        view_func = MagicMock()
        decorated_view_func = project_membership_required(view_func=view_func)
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[project.id])
        )
        request.user = LabAdminUserFactory()
        decorated_view_func(request=request, project_id=project.id)
        view_func.assert_called_once_with(request, project.id)

    @staticmethod
    def test_project_member_passes_check():
        project = ProjectWithLeaderFactory()
        view_func = MagicMock()
        decorated_view_func = project_membership_required(view_func=view_func)
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[project.id])
        )
        request.user = project.leader.user
        decorated_view_func(request=request, project_id=project.id)
        view_func.assert_called_once_with(request, project.id)

    @staticmethod
    def test_no_membership_raises_403():
        project = ProjectFactory()
        view_func = MagicMock()
        decorated_view_func = project_membership_required(view_func=view_func)
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[project.id])
        )
        request.user = StaffUserFactory()
        result = decorated_view_func(request=request, project_id=project.id)
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403

    @staticmethod
    def test_no_project_raises_404():
        view_func = MagicMock()
        decorated_view_func = project_membership_required(view_func=view_func)
        request = RequestFactory().get(
            reverse("api:presigned_document_upload_url", args=[1])
        )
        request.user = LabAdminUserFactory.build()
        result = decorated_view_func(request=request, project_id=1)
        assert isinstance(result, JsonResponse)
        assert result.status_code == 404
