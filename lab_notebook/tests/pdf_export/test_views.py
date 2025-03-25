from unittest import mock

from django.test import RequestFactory, TestCase
from slugify import slugify

from euphro_auth.tests import factories as auth_factories
from lab.measuring_points.models import MeasuringPoint, MeasuringPointImage
from lab.objects.models import RunObjectGroup, RunObjetGroupImage
from lab.tests import factories as lab_factories
from lab_notebook.pdf_export.views import (
    _get_run_data,
    _prepare_images,
)

EXPORT_PDF_URL = "/lab/run/%s/notebook/export-pdf"


class PDFExportTestCase(TestCase):

    def test_export_notebook_to_pdf_view__permission_denied(self):
        run = lab_factories.RunFactory()

        request = RequestFactory()
        request.user = auth_factories.StaffUserFactory()

        self.client.force_login(request.user)

        response = self.client.get(EXPORT_PDF_URL % run.id)

        assert response.status_code == 403

    @mock.patch("lab_notebook.pdf_export.views._prepare_images")
    @mock.patch("lab_notebook.pdf_export.views.create_pdf")
    def test_export_notebook_to_pdf_view__valid_request(
        self, create_pdf_mock: mock.MagicMock, prepare_images_mock: mock.MagicMock
    ):
        # Setup mocks
        prepare_images_mock.return_value = [
            {
                "file_name": "image.png",
                "url": "http://test.com/image.png",
                "transform": {"width": 100, "height": 100, "x": 0, "y": 0},
                "point_locations": [
                    ("001", {"width": 55, "height": 55, "x": 2, "y": 3})
                ],
                "content": b"image content",
                "object_group_label": "Test Object Group",
            }
        ]

        # Setup test data
        request = RequestFactory()
        request.user = auth_factories.LabAdminUserFactory()  # type: ignore

        run = lab_factories.RunFactory()
        og = lab_factories.ObjectGroupFactory()

        rog = RunObjectGroup.objects.create(run=run, objectgroup=og)
        rogi = RunObjetGroupImage.objects.create(
            run_object_group=rog,
            path="path/image.png",
            transform={"width": 100, "height": 100, "x": 0, "y": 0},
        )

        point = MeasuringPoint.objects.create(
            name="001", run=run, object_group=og, comments="comments"
        )
        MeasuringPointImage.objects.create(
            measuring_point=point,
            run_object_group_image=rogi,
            point_location={"width": 55, "height": 55, "x": 2, "y": 3},
        )

        # Call view
        self.client.force_login(request.user)
        response = self.client.get(EXPORT_PDF_URL % run.id)

        # Assertions
        assert response.headers["Content-Type"] == "application/pdf"
        assert response.headers["Content-Disposition"] == (
            f"attachment; filename={slugify(run.label)}_{run.project.slug}.pdf"
        )

        assert prepare_images_mock.call_count == 1
        assert create_pdf_mock.call_count == 1

        # Check create_pdf args
        assert create_pdf_mock.call_args[1]["run"] == {
            "label": run.label,
            "project": {"slug": run.project.slug, "name": run.project.name},
            "particle_type": run.particle_type,
            "energy_in_keV": run.energy_in_keV,
            "beamline": run.beamline,
            "run_notebook": {"comments": run.run_notebook.comments},
        }
        assert "run_methods" in create_pdf_mock.call_args[1]
        assert (
            create_pdf_mock.call_args[1]["images"] == prepare_images_mock.return_value
        )


class PDFExportFunctionTestCase(TestCase):

    @mock.patch("lab_notebook.pdf_export.views.get_storage_info_for_project_images")
    def test_get_run_data(self, mock_get_storage_info):
        # Setup mock
        mock_get_storage_info.return_value = {
            "base_url": "http://test.com",
            "token": "test_token",
        }

        # Setup test data
        run = lab_factories.RunFactory()
        og = lab_factories.ObjectGroupFactory()

        rog = RunObjectGroup.objects.create(run=run, objectgroup=og)
        rogi = RunObjetGroupImage.objects.create(
            run_object_group=rog,
            path="path/image.png",
            transform={"width": 100, "height": 100, "x": 0, "y": 0},
        )

        point = MeasuringPoint.objects.create(
            name="001", run=run, object_group=og, comments="comments"
        )
        MeasuringPointImage.objects.create(
            measuring_point=point,
            run_object_group_image=rogi,
            point_location={"width": 55, "height": 55, "x": 2, "y": 3},
        )

        # Call function
        result_run, result_images, result_storage_info, result_points = _get_run_data(
            run.id
        )

        # Assertions
        assert result_run == run
        assert len(result_images) == 1
        assert result_images[0].id == rogi.id
        assert result_storage_info == mock_get_storage_info.return_value
        assert len(result_points) == 1
        assert result_points[0]["name"] == "001"
        assert result_points[0]["comments"] == "comments"
        assert result_points[0]["object_group"]["label"] == og.label

    @mock.patch("lab_notebook.pdf_export.views._get_image_content")
    def test_prepare_images(self, get_image_content_mock):
        # Setup mocks
        get_image_content_mock.return_value = b"image content"

        # Setup test data
        image = mock.MagicMock()
        image.path = "path/image.png"
        image.file_name = "image.png"
        image.transform = {"width": 100, "height": 100, "x": 0, "y": 0}
        image.measuring_point_images.values_list.return_value = [
            ("001", {"width": 55, "height": 55, "x": 2, "y": 3})
        ]
        image.run_object_group.objectgroup.label = "Test Object Group"

        storage_info = {"base_url": "http://test.com", "token": "token123"}

        # Call function
        result = _prepare_images([image], storage_info)

        # Assertions
        assert len(result) == 1
        assert result[0]["file_name"] == "image.png"
        assert "path/image.png" in result[0]["url"]
        assert result[0]["transform"] == {"width": 100, "height": 100, "x": 0, "y": 0}
        assert result[0]["point_locations"] == [
            ("001", {"width": 55, "height": 55, "x": 2, "y": 3})
        ]
        assert result[0]["content"] == b"image content"
        assert result[0]["object_group_label"] == "Test Object Group"

        # Verify image content was fetched
        assert get_image_content_mock.called
