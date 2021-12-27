from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.http.response import JsonResponse
from django.test import RequestFactory, TestCase
from django.test.testcases import SimpleTestCase
from django.urls import reverse

from ...documents.api_views import (
    presigned_document_delete_url_view,
    presigned_document_download_url_view,
    presigned_document_list_url_view,
    presigned_document_upload_url_view,
)
from ..factories import LabAdminUserFactory, ProjectWithLeaderFactory, StaffUserFactory


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_upload_post")
def test_presigned_document_upload_url_successful_response(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_upload_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_list_url")
def test_presigned_document_list_url_successful_response(project_mocked, s3_fn_mocked):
    request = RequestFactory().get(reverse("api:presigned_document_list_url", args=[1]))
    request.user = LabAdminUserFactory.build()
    response = presigned_document_list_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_download_url")
def test_presigned_presigned_document_download_url_successful_response(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_download_url", args=[1]), 1
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_download_url")
def test_presigned_presigned_document_download_url_no_key_sends_bad_requests(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        reverse("api:presigned_document_download_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_download_url")
def test_presigned_presigned_document_download_url_wrong_key_sends_bad_requests(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_download_url", args=[1]), 2
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_delete_url")
def test_presigned_document_delete_url_successful_response(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_delete_url", args=[1]), 1
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_delete_url")
def test_presigned_document_delete_url_no_key_sends_bad_requests(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        reverse("api:presigned_document_delete_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects")
@patch("lab.documents.object_storage.create_presigned_document_delete_url")
def test_presigned_document_delete_url_wrong_key_sends_bad_requests(
    project_mocked, s3_fn_mocked
):
    request = RequestFactory().get(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_delete_url", args=[1]), 2
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content
