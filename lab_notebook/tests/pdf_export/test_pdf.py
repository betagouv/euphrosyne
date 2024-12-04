import base64
import tempfile
from io import BytesIO
from unittest import mock

from django.utils.translation import gettext as _
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import HRFlowable, Paragraph, Table

from ...pdf_export.pdf import (
    MeasuringPointTitle,
    create_pdf,
    draw_image_with_points,
    generate_image_with_points,
    generate_measuring_points_story,
    get_analysis_info,
)

# pylint: disable=line-too-long
BASE_64_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAQAAACUXCEZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfoBhUMIihFWXb8AAABqUlEQVR42u3RoQ0CQQAAwf3POTQJJUA5r2kRQR0YNBXQAZKnCNxltoSdpa1jmrO9++jWq48XU3buO1q69vRiyh6tqwtzBxiwAAuwAAuwAAswYAEWYAEWYAEWYMACLMACLMACLMACDFiABViABViABRiwAAuwAAuwAAswYAEWYAEWYAEWYAEGLMACLMACLMACDFiABViABViABRiwBYAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIAFGLAAC7AAC7AACzBgARZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFGLAAC7AAC7AAC7AAAxZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswPq/UV0wT9qhlt6dnJi0ve0HP9AMF2SGvsYAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjQtMDYtMjFUMTI6MzQ6NDArMDA6MDBepWMLAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI0LTA2LTIxVDEyOjM0OjQwKzAwOjAwL/jbtwAAAABJRU5ErkJggg=="
BASE_NOTEBOOK_IMAGE = {
    "object_group_label": "test",
    "file_name": "test.png",
    "url": "http://test.com/test.png",
    "transform": None,
    "point_locations": [("test", {"x": 0, "y": 0, "width": 10, "height": 10})],
    "content": BytesIO(base64.b64decode(BASE_64_IMAGE)),
}


def test_draw_image_with_points__creates_image():
    with tempfile.NamedTemporaryFile("w+b", suffix=".png", delete_on_close=False) as f:
        draw_image_with_points(
            BASE_NOTEBOOK_IMAGE,
            f.name,
        )
        f.close()

        assert Image.open(f.name)


def test_draw_image_with_points__crops():
    with tempfile.NamedTemporaryFile("w+b", suffix=".png", delete_on_close=False) as f:
        draw_image_with_points(
            {
                **BASE_NOTEBOOK_IMAGE,
                "transform": {"x": 0, "y": 0, "width": 100, "height": 100},
            },
            f.name,
        )
        f.close()

        image = Image.open(f.name)
        assert image.size == (100, 100)


def test_draw_image_with_points__very_small_image_font():
    with tempfile.NamedTemporaryFile("w+b", suffix=".png", delete_on_close=False) as f:
        draw_image_with_points(
            {
                **BASE_NOTEBOOK_IMAGE,
                "transform": {"x": 0, "y": 0, "width": 1, "height": 1},
            },
            f.name,
        )
        f.close()

        assert Image.open(f.name)


def test_draw_image_with_points__add_points():
    with tempfile.NamedTemporaryFile("w+b", suffix=".png") as f:
        draw_mock = mock.MagicMock()
        with mock.patch(
            "lab_notebook.pdf_export.pdf.ImageDraw.Draw",
            mock.MagicMock(return_value=draw_mock),
        ):
            draw_image_with_points(
                {
                    **BASE_NOTEBOOK_IMAGE,
                    "point_locations": [
                        ("test-1", {"x": 0, "y": 0, "width": 10, "height": 10}),
                        ("test-2", {"x": 15, "y": 15}),
                    ],
                },
                f.name,
            )
            draw_mock.ellipse.assert_called_once()
            draw_mock.rectangle.assert_called_once()
            draw_mock.text.assert_called()


def test_generate_image_with_points():
    with tempfile.TemporaryDirectory() as temp_dir:
        measuring_point = {
            "name": "point-test",
            "comments": "test",
            "object_group": {
                "label": "object test",
            },
        }
        measuring_point_images = {
            "point-test": BASE_NOTEBOOK_IMAGE,
        }

        pdf_image = generate_image_with_points(
            measuring_point, measuring_point_images, temp_dir, max_height=1, max_width=1
        )

        assert Image.open(f"{temp_dir}/point-test-{BASE_NOTEBOOK_IMAGE['file_name']}")
        assert (pdf_image.drawWidth, pdf_image.drawHeight) == (1, 1)


def test_get_analysis_info__object_group():
    measuring_point = {
        "name": "point-test",
        "comments": "test",
        "object_group": {
            "label": "object test",
        },
        "standard": None,
    }
    analysis_type, analysed_entity_label, analysis_type_label = get_analysis_info(
        measuring_point
    )
    assert analysis_type == "object_group"
    assert analysed_entity_label == "object test"
    assert analysis_type_label == _("Object group")


def test_get_analysis_info__standard():
    measuring_point = {
        "name": "point-test",
        "comments": "test",
        "object_group": None,
        "standard": {
            "label": "standard test",
        },
    }
    analysis_type, analysed_entity_label, analysis_type_label = get_analysis_info(
        measuring_point
    )
    assert analysis_type == "standard"
    assert analysed_entity_label == "standard test"
    assert analysis_type_label == _("Standard")


def test_get_analysis_info__none():
    measuring_point = {
        "name": "point-test",
        "comments": "test",
        "object_group": None,
        "standard": None,
    }
    analysis_type, analysed_entity_label, analysis_type_label = get_analysis_info(
        measuring_point
    )
    assert analysis_type is None
    assert analysed_entity_label is None
    assert analysis_type_label == "-"


def test_generate_measuring_points_story():
    measuring_points = [
        {
            "name": "point-test-1",
            "comments": "test comment 1",
            "object_group": {"label": "object test 1"},
            "standard": None,
        },
        {
            "name": "point-test-2",
            "comments": "test comment 2",
            "object_group": None,
            "standard": {"label": "standard test 2"},
        },
    ]
    notebook_images = [
        {
            "object_group_label": "test",
            "file_name": "test.png",
            "url": "http://test.com/test.png",
            "transform": None,
            "point_locations": [
                ("point-test-1", {"x": 0, "y": 0, "width": 10, "height": 10})
            ],
            "content": BytesIO(base64.b64decode(BASE_64_IMAGE)),
        }
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        story = generate_measuring_points_story(
            measuring_points, notebook_images, temp_dir
        )

        assert isinstance(story, list)
        assert len(story) > 0
        assert isinstance(story[0], Paragraph)
        assert story[0].text == _("Measuring points")

        # Check first measuring point
        assert isinstance(story[1], MeasuringPointTitle)
        assert story[1].measuring_point_name == "point-test-1"
        assert story[1].analysis_type == "object_group"
        assert story[1].analysed_entity_label == "object test 1"

        assert isinstance(story[2], Table)
        # pylint: disable=protected-access
        assert len(story[2]._cellvalues[0]) == 2  # Two columns: analysis info and image

        assert isinstance(story[3], Paragraph)
        assert story[3].text == _("Comments")

        assert isinstance(story[4], Paragraph)
        assert story[4].text == "test comment 1"

        assert isinstance(story[5], HRFlowable)

        # Check second measuring point
        assert isinstance(story[6], MeasuringPointTitle)
        assert story[6].measuring_point_name == "point-test-2"
        assert story[6].analysis_type == "standard"
        assert story[6].analysed_entity_label == "standard test 2"

        assert isinstance(story[7], Table)
        # pylint: disable=protected-access
        assert len(story[7]._cellvalues[0]) == 1  # One column: analysis info

        assert isinstance(story[8], Paragraph)
        assert story[8].text == _("Comments")

        assert isinstance(story[9], Paragraph)
        assert story[9].text == "test comment 2"

        assert isinstance(story[10], HRFlowable)


def test_create_pdf():
    run = {
        "label": "test-run",
        "project": {"slug": "test-project", "name": "Test Project"},
        "particle_type": "electron",
        "energy_in_keV": "100",
        "beamline": "test-beamline",
        "run_notebook": {"comments": "Test comments"},
    }
    run_methods = [
        mock.Mock(
            name="Test Method",
            detectors=[
                mock.Mock(
                    name="Test Detector",
                    filters=["Test Filter"],
                )
            ],
        )
    ]
    measuring_points = [
        {
            "name": "point-test-1",
            "comments": "test comment 1",
            "object_group": {"label": "object test 1"},
            "standard": None,
        },
        {
            "name": "point-test-2",
            "comments": "test comment 2",
            "object_group": None,
            "standard": {"label": "standard test 2"},
        },
    ]
    images = [
        {
            "object_group_label": "test",
            "file_name": "test.png",
            "url": "http://test.com/test.png",
            "transform": None,
            "point_locations": [
                ("point-test-1", {"x": 0, "y": 0, "width": 10, "height": 10})
            ],
            "content": BytesIO(base64.b64decode(BASE_64_IMAGE)),
        }
    ]

    with tempfile.NamedTemporaryFile("w+b", suffix=".pdf", delete=False) as f:
        create_pdf(f.name, run, run_methods, measuring_points, images)
        f.close()

        assert Canvas(f.name, pagesize=A4)


def test_create_pdf_with_no_image():
    run = {
        "label": "test-run",
        "project": {"slug": "test-project", "name": "Test Project"},
        "particle_type": "electron",
        "energy_in_keV": "100",
        "beamline": "test-beamline",
        "run_notebook": {"comments": "Test comments"},
    }
    run_methods = [
        mock.Mock(
            name="Test Method",
            detectors=[
                mock.Mock(
                    name="Test Detector",
                    filters=["Test Filter"],
                )
            ],
        )
    ]
    measuring_points = [
        {
            "name": "point-test-1",
            "comments": "test comment 1",
            "object_group": {"label": "object test 1"},
            "standard": None,
        },
        {
            "name": "point-test-2",
            "comments": "test comment 2",
            "object_group": None,
            "standard": {"label": "standard test 2"},
        },
    ]
    images = []

    with tempfile.NamedTemporaryFile("w+b", suffix=".pdf", delete=False) as f:
        create_pdf(f.name, run, run_methods, measuring_points, images)
        f.close()

        assert Canvas(f.name, pagesize=A4)
