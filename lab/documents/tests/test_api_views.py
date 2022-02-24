from unittest.mock import MagicMock, patch

from django.http.response import JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from ...documents.api_views import (
    presigned_document_delete_url_view,
    presigned_document_download_url_view,
    presigned_document_list_url_view,
    presigned_document_upload_url_view,
)
from ...tests.factories import LabAdminUserFactory


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_document_upload_post",
    MagicMock(return_value=""),
)
def test_presigned_document_upload_url_successful_response():
    request = RequestFactory().post(
        reverse("api:presigned_document_upload_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_upload_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_document_list_url",
    MagicMock(return_value=""),
)
def test_presigned_document_list_url_successful_response():
    request = RequestFactory().post(
        reverse("api:presigned_document_list_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_list_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_download_url",
    MagicMock(return_value=""),
)
def test_presigned_presigned_document_download_url_successful_response():
    request = RequestFactory().post(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_download_url", args=[1]), 1
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_download_url",
    MagicMock(return_value=""),
)
def test_presigned_presigned_document_download_url_no_key_sends_bad_requests():
    request = RequestFactory().post(
        reverse("api:presigned_document_download_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_download_url",
    MagicMock(return_value=""),
)
def test_presigned_presigned_document_download_url_wrong_key_sends_bad_requests():
    request = RequestFactory().post(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_download_url", args=[1]), 2
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_download_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_delete_url",
    MagicMock(return_value=""),
)
def test_presigned_document_delete_url_successful_response():
    request = RequestFactory().post(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_delete_url", args=[1]), 1
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert b"url" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_delete_url",
    MagicMock(return_value=""),
)
def test_presigned_document_delete_url_no_key_sends_bad_requests():
    request = RequestFactory().post(
        reverse("api:presigned_document_delete_url", args=[1])
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content


@patch("lab.models.Project.objects", MagicMock())
@patch(
    "lab.documents.api_views.create_presigned_delete_url",
    MagicMock(return_value=""),
)
def test_presigned_document_delete_url_wrong_key_sends_bad_requests():
    request = RequestFactory().post(
        "{}/?key=projects/{}/documents/".format(
            reverse("api:presigned_document_delete_url", args=[1]), 2
        )
    )
    request.user = LabAdminUserFactory.build()
    response = presigned_document_delete_url_view(request, project_id=1)
    assert isinstance(response, JsonResponse)
    assert response.status_code == 400
    assert b"message" in response.content
