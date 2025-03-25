import typing

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont, ImageOps
from reportlab.lib.units import inch
from reportlab.platypus import Image

if typing.TYPE_CHECKING:
    from .pdf import MeasuringPoint, NotebookImage


# Constants for image processing
DEFAULT_MAX_WIDTH = 3 * inch
DEFAULT_MAX_HEIGHT = 3 * inch


def resize_image(
    img: Image,
    max_width: float = DEFAULT_MAX_WIDTH,
    max_height: float = DEFAULT_MAX_HEIGHT,
):
    """Resize an image to fit within max dimensions while maintaining aspect ratio."""
    aspect_ratio = img.drawWidth / img.drawHeight
    if img.drawWidth > max_width or img.drawHeight > max_height:
        if aspect_ratio > 1:
            # Landscape orientation
            width = max_width
            height = max_width / aspect_ratio
        else:
            # Portrait orientation
            height = max_height
            width = max_height * aspect_ratio
    else:
        width = img.drawWidth
        height = img.drawHeight
    return width, height


def draw_image_with_points(
    image: "NotebookImage", output_path: str
):  # pylint: disable=too-many-locals
    """Draw an image with its measuring points and save to output_path."""
    pil_image: PILImage.ImageFile.ImageFile | PILImage.Image = PILImage.open(
        image["content"]
    )
    # Prevent image rotation
    transposed_image = ImageOps.exif_transpose(pil_image)
    if transposed_image:
        pil_image = transposed_image

    if image["transform"]:
        pil_image = pil_image.crop(
            (
                image["transform"]["x"],
                image["transform"]["y"],
                image["transform"]["x"] + image["transform"]["width"],
                image["transform"]["y"] + image["transform"]["height"],
            )
        )
    draw = ImageDraw.Draw(pil_image)

    ratio = pil_image.width / 1000

    for point_name, location in image["point_locations"]:
        x, y = location["x"], location["y"]
        if not (location.get("width") and location.get("height")):
            r = 10 * ratio
            left_up_point = (x - r, y - r)
            right_down_point = (x + r, y + r)
            draw.ellipse([left_up_point, right_down_point], fill="red")
        else:
            left_right_point = (x, y)
            right_down_point = (x + location["width"], y + location["height"])
            draw.rectangle([left_right_point, right_down_point], outline="red")
        font_size = 35 * ratio
        font = ImageFont.load_default(size=font_size if font_size > 1 else 1)
        draw.text(
            (location["x"] + (20 * ratio), location["y"] - (40 * ratio)),
            point_name,
            fill="red",
            font=font,
        )
    pil_image.save(output_path)


def generate_image_with_points(
    measuring_point: "MeasuringPoint",
    measuring_point_images: dict[str, "NotebookImage"],
    images_temp_dir: str,
    max_width: float = DEFAULT_MAX_WIDTH,
    max_height: float = DEFAULT_MAX_HEIGHT,
):
    """Generate an image with measuring points for a specific measuring point."""
    image = measuring_point_images[measuring_point["name"]]
    file_name = image["file_name"]
    output_path = f"{images_temp_dir}/{measuring_point['name']}-{file_name}"
    draw_image_with_points(image=image, output_path=output_path)
    img = Image(output_path)
    img.drawWidth, img.drawHeight = resize_image(img, max_width, max_height)
    return img
