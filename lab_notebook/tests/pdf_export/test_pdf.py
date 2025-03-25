import base64
import tempfile
from io import BytesIO
from unittest import mock

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from ...pdf_export.pdf import (
    MeasuringPointTitle,
    PDFGenerator,
    create_pdf,
)

# pylint: disable=line-too-long
BASE_64_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAQAAACUXCEZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfoBhUMIihFWXb8AAABqUlEQVR42u3RoQ0CQQAAwf3POTQJJUA5r2kRQR0YNBXQAZKnCNxltoSdpa1jmrO9++jWq48XU3buO1q69vRiyh6tqwtzBxiwAAuwAAuwAAswYAEWYAEWYAEWYMACLMACLMACLMACDFiABViABViABRiwAAuwAAuwAAswYAEWYAEWYAEWYAEGLMACLMACLMACDFiABViABViABRiwBYAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIAFGLAAC7AAC7AACzBgARZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFGLAAC7AAC7AAC7AAAxZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswPq/UV0wT9qhlt6dnJi0ve0HP9AMF2SGvsYAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjQtMDYtMjFUMTI6MzQ6NDArMDA6MDBepWMLAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI0LTA2LTIxVDEyOjM0OjQwKzAwOjAwL/jbtwAAAABJRU5ErkJggg=="


def test_measuring_point_title_initialization():
    # Create a valid style for the test

    styles = getSampleStyleSheet()

    title = MeasuringPointTitle(
        "Test Point",
        styles["Heading1"],
        analysis_type="object_group",
        analysed_entity_label="Test Object",
    )

    assert title.measuring_point_name == "Test Point"
    assert title.analysis_type == "object_group"
    assert title.analysed_entity_label == "Test Object"


@mock.patch("lab_notebook.pdf_export.pdf.PDFGenerator")
def test_create_pdf(pdf_generator_mock):
    # Test data
    run = {
        "label": "test-run",
        "project": {"slug": "test-project", "name": "Test Project"},
        "particle_type": "electron",
        "energy_in_keV": "100",
        "beamline": "test-beamline",
        "run_notebook": {"comments": "Test comments"},
    }
    run_methods = [mock.MagicMock()]
    measuring_points = [
        {"name": "test-point", "comments": "", "object_group": None, "standard": None}
    ]
    images = [
        {
            "object_group_label": "test",
            "file_name": "test.png",
            "url": "http://test.com/test.png",
            "transform": None,
            "point_locations": [],
            "content": BytesIO(base64.b64decode(BASE_64_IMAGE)),
        }
    ]

    # Test function
    with tempfile.NamedTemporaryFile("w+b", suffix=".pdf") as f:
        create_pdf(f.name, run, run_methods, measuring_points, images)

        # Verify PDFGenerator was called with correct context
        context = pdf_generator_mock.call_args[0][0]
        assert context["run"] == run
        assert context["run_methods"] == run_methods
        assert context["measuring_points"] == measuring_points
        assert context["images"] == images
        assert "temp_dir" in context

        # Verify create_pdf was called
        pdf_generator_instance = pdf_generator_mock.return_value
        assert pdf_generator_instance.create_pdf.called
        assert pdf_generator_instance.create_pdf.call_args[0][0] == f.name


@mock.patch("lab_notebook.pdf_export.pdf.render_markdown_to_paragraphs")
@mock.patch("lab_notebook.pdf_export.pdf.CustomDocTemplate")
def test_pdf_generator(doc_template_mock, render_markdown_mock):
    # Setup mocks

    styles = getSampleStyleSheet()
    render_markdown_mock.return_value = [
        Paragraph("Rendered markdown", styles["Normal"])
    ]

    # Test data
    context = {
        "run": {
            "label": "test-run",
            "project": {"slug": "test-project", "name": "Test Project"},
            "particle_type": "electron",
            "energy_in_keV": "100",
            "beamline": "test-beamline",
            "run_notebook": {"comments": "Test comments"},
        },
        "run_methods": [],
        "measuring_points": [],
        "images": [],
        "temp_dir": "/tmp",
    }

    # Create instance and test methods
    generator = PDFGenerator(context)

    # Test _add_comments
    generator._add_comments()  # pylint: disable=protected-access
    assert render_markdown_mock.called
    assert render_markdown_mock.call_args[0][0] == "Test comments"

    # Test create_pdf
    generator.create_pdf("/tmp/test.pdf")
    assert doc_template_mock.called
    assert doc_template_mock.return_value.multiBuild.called


@mock.patch("lab_notebook.pdf_export.pdf.PDFGenerator")
def test_create_pdf_with_no_image(pdf_generator_mock):
    run = {
        "label": "test-run",
        "project": {"slug": "test-project", "name": "Test Project"},
        "particle_type": "electron",
        "energy_in_keV": "100",
        "beamline": "test-beamline",
        "run_notebook": {"comments": "Test comments"},
    }
    run_methods = [mock.MagicMock()]
    measuring_points = [
        {"name": "test-point", "comments": "", "object_group": None, "standard": None}
    ]
    images = []

    with tempfile.NamedTemporaryFile("w+b", suffix=".pdf", delete=False) as f:
        create_pdf(f.name, run, run_methods, measuring_points, images)

        # Verify PDFGenerator was called with empty images list
        context = pdf_generator_mock.call_args[0][0]
        assert context["images"] == []
