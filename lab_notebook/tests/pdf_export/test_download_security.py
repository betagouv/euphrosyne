from pathlib import Path
from unittest import mock

import pytest
from django.test import RequestFactory

from euphro_auth.tests.factories import LabAdminUserFactory
from euphro_tools.exceptions import EuphroToolsException
from lab.measuring_points.models import MeasuringPoint, MeasuringPointImage
from lab.objects.models import RunObjectGroup, RunObjetGroupImage
from lab.tests import factories
from lab_notebook.pdf_export.views import (
    _get_image_content,
    export_notebook_to_pdf_view,
)
from shared.http import DownloadError

AZURE_ORIGIN = "https://account.blob.core.windows.net"
POP_ORIGIN = "https://iiif.prd.cloud.culture.fr"


@pytest.fixture(autouse=True)
def image_origins(settings):
    settings.PDF_EXPORT_AZURE_IMAGE_ORIGINS = [AZURE_ORIGIN]
    settings.EROS_BASE_IMAGE_URL = "http://10.12.0.5:8080"
    settings.EUPHROSYNE_TOOLS_API_URL = "http://127.0.0.1:8001"


@pytest.mark.parametrize(
    "provider,url",
    [
        ("azure", f"{AZURE_ORIGIN}/project/image.jpg?sig=test-sas"),
        ("eros", "http://10.12.0.5:8080/iiif/image.jpg?token=test-eros"),
        ("pop", f"{POP_ORIGIN}/iiif/3/joconde/image.jpg"),
    ],
)
@mock.patch("shared.http.requests.get")
def test_authorized_image_download(mock_get, provider, url):
    response = mock.Mock(status_code=200, content=b"image content")
    mock_get.return_value = response
    assert _get_image_content(url, provider).read() == b"image content"
    mock_get.assert_called_once_with(
        url, timeout=10, headers=None, allow_redirects=False
    )
    response.close.assert_called_once()


@mock.patch("shared.http.requests.get")
def test_eros_proxy_uses_explicit_internal_tools_origin(mock_get, settings):
    settings.EROS_BASE_IMAGE_URL = None
    mock_get.return_value = mock.Mock(status_code=200, content=b"image content")
    url = "http://127.0.0.1:8001/eros/iiif/image.jpg?token=test-jwt"
    assert _get_image_content(url, "eros").read() == b"image content"
    mock_get.assert_called_once_with(
        url, timeout=10, headers=None, allow_redirects=False
    )


@pytest.mark.parametrize(
    "provider,url",
    [
        ("azure", f"{POP_ORIGIN}/image.jpg?sig=test-sas"),
        ("azure", "http://10.12.0.5:8080/image.jpg?sig=test-sas"),
        ("azure", "http://127.0.0.1:8001/image.jpg?sig=test-sas"),
        ("eros", f"{AZURE_ORIGIN}/image.jpg?token=test-eros"),
        ("eros", "http://10.12.0.6:8080/image.jpg"),
        ("eros", "https://10.12.0.5:8080/image.jpg"),
        ("eros", "http://10.12.0.5:8081/image.jpg"),
        ("pop", f"{AZURE_ORIGIN}/image.jpg"),
        ("pop", "http://iiif.prd.cloud.culture.fr/image.jpg"),
        ("pop", "https://iiif.prd.cloud.culture.fr:444/image.jpg"),
        ("pop", "http://10.12.0.5:8080/image.jpg"),
    ],
)
@mock.patch("shared.http.requests.get")
def test_provider_origins_are_not_interchangeable(mock_get, provider, url):
    with pytest.raises(DownloadError):
        _get_image_content(url, provider)
    mock_get.assert_not_called()


@mock.patch("shared.http.requests.get")
def test_azure_requires_explicit_https_origin(mock_get, settings):
    settings.PDF_EXPORT_AZURE_IMAGE_ORIGINS = []
    with pytest.raises(DownloadError):
        _get_image_content(f"{AZURE_ORIGIN}/image.jpg", "azure")
    settings.PDF_EXPORT_AZURE_IMAGE_ORIGINS = ["http://account.blob.core.windows.net"]
    with pytest.raises(DownloadError):
        _get_image_content("http://account.blob.core.windows.net/image.jpg", "azure")
    mock_get.assert_not_called()


@pytest.mark.django_db
@mock.patch("lab_notebook.pdf_export.views.create_pdf")
@mock.patch("lab_notebook.pdf_export.views._get_image_content")
@mock.patch("lab_notebook.pdf_export.views.get_storage_info_for_project_images")
def test_project_access_precedes_all_external_export_calls(
    mock_storage, mock_image, mock_pdf, project_api_context
):
    context = project_api_context
    mock_storage.return_value = {"base_url": AZURE_ORIGIN, "token": "test-sas"}
    response = context.client.get(f"/lab/run/{context.run.pk}/notebook/export-pdf")
    if context.can_access_project:
        assert response.status_code == 200
        mock_storage.assert_called_once_with(context.project.slug)
        mock_pdf.assert_called_once()
    else:
        assert response.status_code in {302, 403}
        mock_storage.assert_not_called()
        mock_image.assert_not_called()
        mock_pdf.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "provider,path",
    [
        ("azure", "/project/image.jpg"),
        ("eros", "C2RMF12345/67890"),
        ("eros_proxy", "F12345/67890"),
        ("pop", "/iiif/3/joconde%2F12345%2Fimage.jpg/full/max/0/default.jpg"),
    ],
)
@mock.patch("lab_notebook.pdf_export.views.create_pdf")
@mock.patch("shared.http.requests.get")
def test_export_with_authorized_provider_image(
    mock_get, mock_pdf, settings, provider, path
):
    if provider == "eros_proxy":
        settings.EROS_BASE_IMAGE_URL = None
    run, request = _export_request_with_image(path)
    storage_response = mock.Mock(status_code=200)
    storage_response.json.return_value = {"base_url": AZURE_ORIGIN, "token": "test-sas"}
    image_response = mock.Mock(status_code=200, content=b"image content")
    mock_get.side_effect = [storage_response, image_response]
    mock_pdf.side_effect = lambda **kwargs: Path(kwargs["path"]).write_bytes(
        b"test pdf"
    )

    response = export_notebook_to_pdf_view(request, str(run.pk))

    assert response.status_code == 200
    assert response.content == b"test pdf"
    assert mock_get.call_count == 2
    assert all(
        call.kwargs["allow_redirects"] is False for call in mock_get.call_args_list
    )
    images = mock_pdf.call_args.kwargs["images"]
    assert len(images) == 1
    assert images[0]["content"].read() == b"image content"
    assert images[0]["point_locations"][0][0] == "001"


def _export_request_with_image(path):
    run = factories.RunFactory()
    group = RunObjectGroup.objects.create(
        run=run, objectgroup=factories.ObjectGroupFactory()
    )
    image = RunObjetGroupImage.objects.create(run_object_group=group, path=path)
    point = MeasuringPoint.objects.create(name="001", run=run)
    MeasuringPointImage.objects.create(
        measuring_point=point,
        run_object_group_image=image,
        point_location={"width": 10, "height": 10, "x": 0, "y": 0},
    )
    request = RequestFactory().get(f"/lab/run/{run.pk}/notebook/export-pdf")
    request.user = LabAdminUserFactory()
    return run, request


@pytest.mark.django_db
@mock.patch("lab_notebook.pdf_export.views.create_pdf")
@mock.patch("shared.http.requests.get")
def test_export_refuses_untrusted_storage_url_without_disclosing_token(
    mock_get, mock_pdf
):
    run, request = _export_request_with_image("/project/image.jpg")
    storage_response = mock.Mock(status_code=200)
    storage_response.json.return_value = {
        "base_url": "http://169.254.169.254",
        "token": "private-test-token",
    }
    mock_get.return_value = storage_response
    response = export_notebook_to_pdf_view(request, str(run.pk))
    assert response.status_code == 502
    assert b"private-test-token" not in response.content
    assert mock_get.call_count == 1  # Only Tools API; no image request.
    mock_pdf.assert_not_called()


@pytest.mark.django_db
@mock.patch("lab_notebook.pdf_export.views.create_pdf")
@mock.patch("shared.http.requests.get")
def test_image_redirect_aborts_export_without_contacting_target(mock_get, mock_pdf):
    run, request = _export_request_with_image("/project/image.jpg")
    storage_response = mock.Mock(status_code=200)
    storage_response.json.return_value = {"base_url": AZURE_ORIGIN, "token": "test-sas"}
    image_response = mock.Mock(
        status_code=302,
        headers={"Location": "http://169.254.169.254/?token=private-test-token"},
    )
    mock_get.side_effect = [storage_response, image_response]
    response = export_notebook_to_pdf_view(request, str(run.pk))
    assert response.status_code == 502
    assert b"private-test-token" not in response.content
    assert mock_get.call_count == 2  # Storage and original image only.
    image_response.close.assert_called_once()
    mock_pdf.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("error", [DownloadError, EuphroToolsException])
@mock.patch("lab_notebook.pdf_export.views._prepare_images")
@mock.patch("lab_notebook.pdf_export.views.get_storage_info_for_project_images")
def test_export_returns_controlled_upstream_error(mock_storage, mock_images, error):
    run, request = _export_request_with_image("/project/image.jpg")
    mock_storage.side_effect = error("private-test-token")
    response = export_notebook_to_pdf_view(request, str(run.pk))
    assert response.status_code == 502
    assert b"private-test-token" not in response.content
    mock_images.assert_not_called()
