import base64
import tempfile
from io import BytesIO
from unittest import mock

from PIL import Image

from lab_notebook.pdf_export.image_utils import (
    DEFAULT_MAX_WIDTH,
    draw_image_with_points,
    generate_image_with_points,
    resize_image,
)

# Test image in base64 format
BASE_64_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAQAAACUXCEZAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElNRQfoBhUMIihFWXb8AAABqUlEQVR42u3RoQ0CQQAAwf3POTQJJUA5r2kRQR0YNBXQAZKnCNxltoSdpa1jmrO9++jWq48XU3buO1q69vRiyh6tqwtzBxiwAAuwAAuwAAswYAEWYAEWYAEWYMACLMACLMACLMACDFiABViABViABRiwAAuwAAuwAAswYAEWYAEWYAEWYAEGLMACLMACLMACDFiABViABViABRiwBYAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIAFGLAAC7AAC7AACzBgARZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFGLAAC7AAC7AAC7AAAxZgARZgARZgAQYswAIswAIswAIMWIAFWIAFWIAFWIABC7AAC7AAC7AAAxZgARZgARZgARZgwAIswAIswAIswIAFWIAFWIAFWIABC7AAC7AAC7AACzBgARZgARZgARZgwAIswAIswPq/UV0wT9qhlt6dnJi0ve0HP9AMF2SGvsYAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjQtMDYtMjFUMTI6MzQ6NDArMDA6MDBepWMLAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI0LTA2LTIxVDEyOjM0OjQwKzAwOjAwL/jbtwAAAABJRU5ErkJggg=="  # pylint: disable=line-too-long

# Base notebook image for testing
BASE_NOTEBOOK_IMAGE = {
    "object_group_label": "test",
    "file_name": "test.png",
    "url": "http://test.com/test.png",
    "transform": None,
    "point_locations": [("test", {"x": 0, "y": 0, "width": 10, "height": 10})],
    "content": BytesIO(base64.b64decode(BASE_64_IMAGE)),
}


def test_resize_image():
    # Create a mock image
    img = mock.MagicMock()
    img.drawWidth = 200
    img.drawHeight = 100

    # Test landscape orientation resize
    width, height = resize_image(img, max_width=100, max_height=100)
    assert width == 100
    assert height == 50  # Aspect ratio maintained

    # Test portrait orientation resize
    img.drawWidth = 100
    img.drawHeight = 200
    width, height = resize_image(img, max_width=100, max_height=100)
    assert width == 50  # Aspect ratio maintained
    assert height == 100

    # Test no resize needed
    img.drawWidth = 50
    img.drawHeight = 50
    width, height = resize_image(img, max_width=100, max_height=100)
    assert width == 50
    assert height == 50

    # Test default parameters
    img.drawWidth = 500
    img.drawHeight = 300
    width, height = resize_image(img)
    assert width == DEFAULT_MAX_WIDTH
    assert height == DEFAULT_MAX_WIDTH / (img.drawWidth / img.drawHeight)


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
            "lab_notebook.pdf_export.image_utils.ImageDraw.Draw",
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
