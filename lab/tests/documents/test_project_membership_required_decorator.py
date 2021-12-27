from unittest.mock import MagicMock, patch

from django.http.response import JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from ...documents.api_views import project_membership_required
from ...models import Project
from ..factories import LabAdminUserFactory, StaffUserFactory


@patch("lab.models.Project.objects")
def test_admin_user_passes_check(project_mocked):
    view_func = MagicMock()
    decorated_view_func = project_membership_required(view_func=view_func)
    request = RequestFactory().get(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    decorated_view_func(request=request, project_id=1)
    view_func.assert_called_once_with(request, 1)


@patch("lab.models.Project.objects")
def test_project_member_passes_check(project_mocked):
    view_func = MagicMock()
    decorated_view_func = project_membership_required(view_func=view_func)
    request = RequestFactory().get(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = StaffUserFactory.build()
    project_mocked.get.return_value.members.filter.return_value.exists.return_value = (
        True
    )
    decorated_view_func(request=request, project_id=1)
    view_func.assert_called_once_with(request, 1)


@patch("lab.models.Project.objects")
def test_no_membership_raises_403(project_mocked):
    view_func = MagicMock()
    decorated_view_func = project_membership_required(view_func=view_func)
    request = RequestFactory().get(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = StaffUserFactory.build()
    project_mocked.get.return_value.members.filter.return_value.exists.return_value = (
        False
    )
    result = decorated_view_func(request=request, project_id=1)
    assert isinstance(result, JsonResponse)
    assert result.status_code == 403


@patch("lab.models.Project.objects")
def test_no_project_raises_404(project_mocked):
    view_func = MagicMock()
    decorated_view_func = project_membership_required(view_func=view_func)
    request = RequestFactory().get(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    project_mocked.get.side_effect = Project.DoesNotExist()
    result = decorated_view_func(request=request, project_id=1)
    assert isinstance(result, JsonResponse)
    assert result.status_code == 404
