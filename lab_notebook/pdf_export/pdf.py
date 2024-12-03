import tempfile
import typing
from io import BytesIO

from django.utils.translation import gettext as _
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

if typing.TYPE_CHECKING:
    from lab.methods.dto import MethodDTO

styles = getSampleStyleSheet()


# Define TypedDicts for type hinting
class Transform(typing.TypedDict):
    width: float
    height: float
    x: float
    y: float


class PointLocation(typing.TypedDict):
    x: float
    y: float
    width: float
    height: float


class NotebookImage(typing.TypedDict):
    object_group_label: str
    file_name: str
    url: str
    transform: Transform | None
    point_locations: list[tuple[str, PointLocation]]  # (name, point_location)
    content: BytesIO


class MeasuringPointObjectGroup(typing.TypedDict):
    label: str


class MeasuringPointStandard(typing.TypedDict):
    label: str


class MeasuringPoint(typing.TypedDict):
    name: str
    comments: str
    object_group: MeasuringPointObjectGroup | None
    standard: MeasuringPointStandard | None


class Project(typing.TypedDict):
    slug: str
    name: str


class Notebook(typing.TypedDict):
    comments: str


class Run(typing.TypedDict):

    label: str
    project: Project
    particle_type: str
    energy_in_keV: int | None
    beamline: str
    run_notebook: Notebook


class MeasuringPointTitle(Paragraph):
    measuring_point_name: str
    analysis_type: typing.Literal["object_group", "standard"] | None
    analysed_entity_label: str | None

    def __init__(
        self,
        text,
        *args,
        analysis_type: typing.Literal["object_group", "standard"] | None = None,
        analysed_entity_label: str | None = None,
        **kwargs,
    ):
        self.measuring_point_name = text
        self.analysed_entity_label = analysed_entity_label
        self.analysis_type = analysis_type
        super().__init__(text, *args, **kwargs)


class CustomDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        # Registers Table of Content entries
        if isinstance(flowable, MeasuringPointTitle):
            toc_entry_text = flowable.measuring_point_name
            if flowable.analysed_entity_label:
                toc_entry_text += f" - {flowable.analysed_entity_label}"
            if flowable.analysis_type:
                text = "OBJ" if flowable.analysis_type == "object_group" else "STD"
                toc_entry_text += f" [{text}]"

            key = f"measuring-point-{flowable.measuring_point_name}"
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (0, toc_entry_text, self.page, key))


def create_pdf(
    path: str,
    run: Run,
    run_methods: list["MethodDTO"],
    measuring_points: list[MeasuringPoint],
    images: list[NotebookImage],
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        doc = CustomDocTemplate(
            path, title=f"{run['label']} - {run['project']['slug']}", pagesize=A4
        )
        story: list[Flowable] = []

        add_project_and_run_info(story, run)
        story.extend(generate_experimental_conditions_story(run, run_methods))
        story.append(Spacer(1, 0.2 * inch))
        add_comments(story, run["run_notebook"]["comments"])
        story.append(Spacer(1, 0.2 * inch))
        story.extend(generate_images_with_points_story(images, tmpdirname))
        story.append(PageBreak())
        add_table_of_contents(story)
        story.append(PageBreak())
        story.extend(
            generate_measuring_points_story(
                measuring_points, notebook_images=images, images_temp_dir=tmpdirname
            )
        )

        doc.multiBuild(story)


def add_project_and_run_info(story, run: Run):
    story.append(Paragraph(_("Project: %s") % run["project"]["name"], styles["Title"]))
    story.append(Paragraph(_("Run: %s") % run["label"], styles["Title"]))


def add_comments(story, comments: str):
    story.append(Paragraph(_("Comments"), styles["Heading2"]))
    story.append(Paragraph(comments or "-", styles["Normal"]))


def add_table_of_contents(story):
    story.append(Paragraph(_("Table of contents"), styles["Heading1"]))
    story.append(TableOfContents())


def generate_experimental_conditions_story(run: Run, run_methods: list["MethodDTO"]):
    story = []
    story.append(Paragraph(_("Experimental conditions"), styles["Heading2"]))
    story.append(
        Paragraph(
            _("Particle type: %s") % (run["particle_type"] or "-"), styles["Normal"]
        )
    )
    story.append(
        Paragraph(_("Energy: %s") % (run["energy_in_keV"] or "-"), styles["Normal"])
    )
    story.append(
        Paragraph(_("Beamline: %s") % (run["beamline"] or "-"), styles["Normal"])
    )

    for method in run_methods:
        story.append(Paragraph(_("Method: %s") % method.name, styles["Heading3"]))
        for detector in method.detectors:
            story.append(Paragraph(_("Detector: %s") % detector.name, styles["Normal"]))
            for detector_filter in detector.filters:
                filter_style = ParagraphStyle(
                    name="Indented",
                    parent=styles["Normal"],
                    leftIndent=10,
                )
                story.append(Paragraph(_("Filter: %s") % detector_filter, filter_style))
    return story


def generate_images_with_points_story(
    images: list[NotebookImage], images_temp_dir: str
):
    story = []
    story.append(Paragraph(_("Run images with point locations"), styles["Heading2"]))
    max_width = 3 * inch
    max_height = 3 * inch

    rendered_images = []
    for image in images:
        file_name = image["file_name"]
        output_path = f"{images_temp_dir}/{file_name}"
        draw_image_with_points(image=image, output_path=output_path)

        img = Image(output_path)
        img.drawWidth, img.drawHeight = resize_image(img, max_width, max_height)

        image_label = Paragraph(image["object_group_label"], styles["Normal"])

        rendered_images.append((img, image_label))

    images_per_row = 2
    images_rows = []
    for i in range(0, len(rendered_images), images_per_row):
        images_rows.append(rendered_images[i : i + images_per_row])  # noqa: E203

    table = Table(images_rows)
    story.append(table)

    return story


def generate_measuring_points_story(  # pylint: disable=too-many-locals
    measuring_points: list[MeasuringPoint],
    notebook_images: list[NotebookImage],
    images_temp_dir: str,
):
    measuring_point_images: dict[str, NotebookImage] = {}
    for image in notebook_images:
        for location in image["point_locations"]:
            measuring_point_images[location[0]] = image

    story = []
    story.append(Paragraph(_("Measuring points"), styles["Heading2"]))
    for measuring_point in measuring_points:
        analysis_type, analysed_entity_label, analysis_type_label = get_analysis_info(
            measuring_point
        )

        point_title = MeasuringPointTitle(
            measuring_point["name"],
            styles["Heading3"],
            analysis_type=analysis_type,
            analysed_entity_label=analysed_entity_label,
        )
        story.append(point_title)

        cols = []
        left_col = []
        left_col.append(Paragraph(_("Analysis type"), styles["Heading4"]))
        left_col.append(Paragraph(analysis_type_label, styles["Normal"]))

        if analysed_entity_label:
            left_col.append(
                Paragraph(
                    _("Reference"),
                    styles["Heading4"],
                )
            )
            left_col.append(
                Paragraph(
                    analysed_entity_label,
                    styles["Normal"],
                )
            )
            cols.append(left_col)

        if measuring_point["name"] in measuring_point_images:
            img = generate_image_with_points(
                measuring_point, measuring_point_images, images_temp_dir
            )
            cols.append([img])

        table = Table([cols])
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (1, 1), "TOP"),
                ]
            )
        )
        story.append(table)

        add_comments(story, measuring_point["comments"])

        story.append(
            HRFlowable(
                width="60%",
                thickness=1,
                lineCap="round",
                color="#ededed",
                spaceBefore=0.3 * inch,
                spaceAfter=0.5 * inch,
            )
        )

    return story


def get_analysis_info(measuring_point: MeasuringPoint):
    analysis_type = None
    analysed_entity_label = None
    analysis_type_label = "-"
    if measuring_point["object_group"]:
        analysis_type = "object_group"
        analysis_type_label = _("Object group")
        analysed_entity_label = measuring_point["object_group"]["label"]
    if measuring_point["standard"]:
        analysis_type = "standard"
        analysis_type_label = _("Standard")
        analysed_entity_label = measuring_point["standard"]["label"]
    return analysis_type, analysed_entity_label, analysis_type_label


def generate_image_with_points(
    measuring_point: MeasuringPoint,
    measuring_point_images: dict[str, NotebookImage],
    images_temp_dir: str,
    max_width: float = 3 * inch,
    max_height: float = 3 * inch,
):
    image = measuring_point_images[measuring_point["name"]]
    file_name = image["file_name"]
    output_path = f"{images_temp_dir}/{measuring_point['name']}-{file_name}"
    draw_image_with_points(image=image, output_path=output_path)
    img = Image(output_path)
    img.drawWidth, img.drawHeight = resize_image(img, max_width, max_height)
    return img


def resize_image(img: Image, max_width: float, max_height: float):
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


def draw_image_with_points(image: NotebookImage, output_path: str):
    pil_image: PILImage.ImageFile.ImageFile | PILImage.Image = PILImage.open(
        image["content"]
    )
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
