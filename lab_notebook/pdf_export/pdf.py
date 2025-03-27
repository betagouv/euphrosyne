import datetime
import tempfile
import typing
from io import BytesIO

from django.utils.translation import gettext as _
from reportlab.lib.styles import ParagraphStyle
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
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents

from .config import (
    BACKGROUND_COLOR,
    CAPTION_STYLE,
    DEFAULT_BORDER_COLOR,
    DEFAULT_BORDER_WIDTH,
    DEFAULT_IMAGE_PADDING,
    DEFAULT_MAX_IMAGE_HEIGHT,
    DEFAULT_MAX_IMAGE_WIDTH,
    HEADING_COLOR,
    IMAGES_PER_ROW,
    INDENTED_STYLE,
    LIGHT_GRAY,
    PAGE_HEIGHT,
    PAGE_MARGIN,
    PAGE_SIZE,
    PAGE_WIDTH,
    PRIMARY_COLOR,
    TEXT_COLOR,
    TOC_ENTRY_STYLE,
    TOC_TITLE_STYLE,
    styles,
)
from .image_utils import (
    draw_image_with_points,
    generate_image_with_points,
    resize_image,
)
from .text_utils import render_markdown_to_paragraphs

# pylint: disable=unused-import,undefined-variable,trailing-whitespace,redefined-outer-name

if typing.TYPE_CHECKING:
    from lab.methods.dto import MethodDTO


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


class PDFContext(typing.TypedDict):
    """Context object for PDF generation to reduce parameter passing"""

    run: Run
    run_methods: list["MethodDTO"]
    measuring_points: list[MeasuringPoint]
    images: list[NotebookImage]
    temp_dir: str


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


class PDFPageTemplate(PageTemplate):
    """Custom page template with header and footer"""

    def __init__(self, template_id, frames, run_label, project_name, **kw):
        self.run_label = run_label
        self.project_name = project_name
        super().__init__(template_id, frames, **kw)

    def afterDrawPage(self, canv, doc):
        """Add header and footer to each page"""
        # Save canvas state
        canv.saveState()

        # Header with logo and project info
        canv.setFillColor(HEADING_COLOR)
        canv.setFont("Helvetica-Bold", 9)
        canv.drawString(PAGE_MARGIN, PAGE_HEIGHT - 30, f"Project: {self.project_name}")

        canv.setFont("Helvetica", 9)
        canv.drawString(PAGE_MARGIN, PAGE_HEIGHT - 45, f"Run: {self.run_label}")

        # Header line
        canv.setStrokeColor(PRIMARY_COLOR)
        canv.setLineWidth(1)
        canv.line(
            PAGE_MARGIN, PAGE_HEIGHT - 55, PAGE_WIDTH - PAGE_MARGIN, PAGE_HEIGHT - 55
        )

        # Footer with page number
        canv.setFont("Helvetica", 9)
        canv.setStrokeColor(LIGHT_GRAY)
        canv.setLineWidth(0.5)
        canv.line(PAGE_MARGIN, 50, PAGE_WIDTH - PAGE_MARGIN, 50)

        canv.setFillColor(TEXT_COLOR)
        page_num = canv.getPageNumber()
        text = f"Page {page_num}"
        canv.drawRightString(PAGE_WIDTH - PAGE_MARGIN, 35, text)

        # Date on footer left
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        canv.drawString(PAGE_MARGIN, 35, f"Generated: {today}")

        # Euphrosyne logo/text in center
        canv.setFillColor(PRIMARY_COLOR)
        canv.drawCentredString(PAGE_WIDTH / 2, 35, "Euphrosyne")

        # Restore canvas state
        canv.restoreState()


class CustomDocTemplate(SimpleDocTemplate):
    """Enhanced document template with custom page layout and TOC support"""

    def __init__(self, filename, **kwargs):
        self.run_label = kwargs.pop("run_label", "")
        self.project_name = kwargs.pop("project_name", "")

        # Set margins
        kwargs.setdefault("leftMargin", PAGE_MARGIN)
        kwargs.setdefault("rightMargin", PAGE_MARGIN)
        kwargs.setdefault("topMargin", PAGE_MARGIN + 40)  # Extra space for header
        kwargs.setdefault("bottomMargin", PAGE_MARGIN + 30)  # Extra space for footer

        super().__init__(filename, **kwargs)

        # Document content area
        content_width = self.width
        content_height = self.height

        # Create frame for the content
        content_frame = Frame(
            PAGE_MARGIN,
            PAGE_MARGIN + 30,  # Bottom margin plus footer height
            content_width,
            content_height,
            id="content",
        )

        # Create page template
        self.addPageTemplates(
            PDFPageTemplate(
                "default", [content_frame], self.run_label, self.project_name
            )
        )

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


class PDFGenerator:
    """Class for generating PDF documents from run data"""

    def __init__(self, context: PDFContext):
        """Initialize with PDF generation context"""
        self.context = context
        self.story: list[Flowable] = []

    def create_pdf(self, output_path: str):
        """Generate a PDF file at the given path"""
        run = self.context["run"]
        run_label = run["label"]
        project_slug = run["project"]["slug"]
        project_name = run["project"]["name"]

        doc = CustomDocTemplate(
            output_path,
            title=f"{run_label} - {project_slug}",
            pagesize=PAGE_SIZE,
            run_label=run_label,
            project_name=project_name,
        )

        self._build_document()
        doc.multiBuild(self.story)

    def _build_document(self):
        """Build the complete PDF document flow"""
        self._add_header()
        self._add_experimental_conditions()

        self.story.append(Spacer(1, 0.2 * inch))

        self._add_comments()

        if self.context["images"]:
            self.story.append(Spacer(1, 0.2 * inch))
            self._add_images_section()

        self.story.append(PageBreak())
        self._add_table_of_contents()

        self.story.append(PageBreak())
        self._add_measuring_points_section()

    def _add_header(self):
        """Add project and run information header"""
        self.story.append(
            Paragraph(
                _("Project: %s") % self.context["run"]["project"]["name"],
                styles["Title"],
            )
        )
        self.story.append(
            Paragraph(_("Run: %s") % self.context["run"]["label"], styles["Title"])
        )

    def _add_experimental_conditions(self):  # pylint: disable=too-many-locals
        """Add experimental conditions section"""

        run = self.context["run"]
        run_methods = self.context["run_methods"]

        self.story.append(Paragraph(_("Experimental conditions"), styles["Heading2"]))

        # Organize basic run info in a table for better layout
        basic_info = [
            [
                Paragraph(_("Particle type") + _(":"), styles["Heading4"]),
                Paragraph(run["particle_type"] or "-", styles["Normal"]),
            ],
            [
                Paragraph(_("Energy") + _(":"), styles["Heading4"]),
                Paragraph(f"{run['energy_in_keV'] or '-'} keV", styles["Normal"]),
            ],
            [
                Paragraph(_("Beamline") + _(":"), styles["Heading4"]),
                Paragraph(run["beamline"] or "-", styles["Normal"]),
            ],
        ]

        # Create table with styling
        info_table = Table(
            basic_info,
            colWidths=[2 * inch, 3 * inch],
            hAlign="LEFT",  # Explicitly set horizontal alignment to left
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                    ("BACKGROUND", (0, 0), (0, -1), BACKGROUND_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            ),
        )
        self.story.append(info_table)
        self.story.append(Spacer(1, 0.2 * inch))

        # If we have methods, add them in a better layout
        if run_methods:
            self.story.append(Paragraph(_("Methods"), styles["Heading3"]))

            for method in run_methods:
                # Create a styled box for the method
                method_title = Paragraph(method.name, styles["Heading4"])

                # Method content table (detectors and filters)
                method_content = []

                for detector in method.detectors:
                    # Detector row
                    detector_row = [
                        Paragraph(_("Detector") + _(":"), styles["Normal"]),
                        Paragraph(detector.name, styles["Normal"]),
                    ]
                    method_content.append(detector_row)

                    # Filters rows (if any)
                    for filter_item in detector.filters:
                        filter_row = [
                            Paragraph(_("Filter") + _(":"), INDENTED_STYLE),
                            Paragraph(filter_item, styles["Normal"]),
                        ]
                        method_content.append(filter_row)

                # Create method details table
                method_table = Table(
                    method_content or [""],  # Reportlab does not accept empty rows
                    colWidths=[inch, 4 * inch],
                    hAlign="LEFT",  # Explicitly set horizontal alignment to left
                    style=TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                            ("BACKGROUND", (0, 0), (0, -1), BACKGROUND_COLOR),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    ),
                )

                # Add method components to story
                self.story.append(method_title)
                self.story.append(method_table)
                self.story.append(Spacer(1, 0.1 * inch))

    def _add_comments(self):
        """Add comments section with markdown support"""
        comments = self.context["run"]["run_notebook"]["comments"]
        self.story.append(Paragraph(_("Comments"), styles["Heading2"]))

        if not comments:
            self.story.append(Paragraph("-", styles["Normal"]))
            return

        # Add markdown-rendered paragraphs
        paragraphs = render_markdown_to_paragraphs(comments, styles)

        # Create a styled container for the comments
        comments_table = Table(
            [[p] for p in paragraphs],
            colWidths=["100%"],
            hAlign="LEFT",  # Explicitly set horizontal alignment to left
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), BACKGROUND_COLOR),
                    ("BOX", (0, 0), (0, -1), 0.5, LIGHT_GRAY),
                    ("LEFTPADDING", (0, 0), (0, -1), 12),
                    ("RIGHTPADDING", (0, 0), (0, -1), 12),
                    ("TOPPADDING", (0, 0), (0, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (0, -1), 6),
                ]
            ),
        )

        self.story.append(comments_table)

    def _add_table_of_contents(self):
        """Add table of contents section"""
        # Add a custom styled title for TOC
        self.story.append(Paragraph(_("Table of contents"), TOC_TITLE_STYLE))

        # Create TOC with custom styling
        toc = TableOfContents()
        toc.levelStyles = [
            TOC_ENTRY_STYLE,
            ParagraphStyle(
                name="TOCEntry1",
                parent=TOC_ENTRY_STYLE,
                leftIndent=20,
                firstLineIndent=0,
            ),
        ]

        # Add the TOC
        self.story.append(toc)

        # Add some space after TOC
        self.story.append(Spacer(1, 0.2 * inch))

    def _add_images_section(self):  # pylint: disable=too-many-locals
        """Add images with point locations section"""

        images = self.context["images"]
        temp_dir = self.context["temp_dir"]

        self.story.append(
            Paragraph(_("Run images with point locations"), styles["Heading2"])
        )

        # Spacer for better layout
        self.story.append(Spacer(1, 0.1 * inch))

        rendered_images = []
        for image in images:
            file_name = image["file_name"]
            output_path = f"{temp_dir}/{file_name}"
            draw_image_with_points(image=image, output_path=output_path)

            img = Image(output_path)
            img.drawWidth, img.drawHeight = resize_image(
                img, DEFAULT_MAX_IMAGE_WIDTH, DEFAULT_MAX_IMAGE_HEIGHT
            )

            # Add border to image
            img.borderColor = DEFAULT_BORDER_COLOR
            img.borderWidth = DEFAULT_BORDER_WIDTH
            img.borderPadding = DEFAULT_IMAGE_PADDING

            # Better caption
            image_label = Paragraph(
                f"<b>{image['object_group_label']}</b>", CAPTION_STYLE
            )

            # Group image and caption in a cell
            image_cell = [img, image_label]
            rendered_images.append(image_cell)

        # Create a table of images with better spacing
        images_rows = []
        for i in range(0, len(rendered_images), IMAGES_PER_ROW):
            row = rendered_images[i : i + IMAGES_PER_ROW]  # noqa: E203

            # Ensure all rows have the same number of cells for proper layout
            while len(row) < IMAGES_PER_ROW:
                row.append("")

            images_rows.append(row)

        # Create table with styling
        col_widths = [DEFAULT_MAX_IMAGE_WIDTH * 1.2] * IMAGES_PER_ROW
        row_heights = [DEFAULT_MAX_IMAGE_HEIGHT * 1.3] * len(images_rows)

        table = Table(
            images_rows,
            colWidths=col_widths,
            rowHeights=row_heights,
            hAlign="LEFT",  # Explicitly set horizontal alignment to left
        )

        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BACKGROUND", (0, 0), (-1, -1), BACKGROUND_COLOR),
                    ("GRID", (0, 0), (-1, -1), 0.5, BACKGROUND_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        self.story.append(table)

    def _add_measuring_points_section(self):  # pylint: disable=too-many-locals
        """Add measuring points section"""

        measuring_points = self.context["measuring_points"]
        notebook_images = self.context["images"]
        temp_dir = self.context["temp_dir"]

        # Create mapping from point name to image
        measuring_point_images: dict[str, NotebookImage] = {}
        for image in notebook_images:
            for location in image["point_locations"]:
                measuring_point_images[location[0]] = image

        self.story.append(Paragraph(_("Measuring points"), styles["Heading2"]))
        self.story.append(Spacer(1, 0.1 * inch))

        for measuring_point in measuring_points:
            analysis_type, analysed_entity_label, analysis_type_label = (
                self._get_analysis_info(measuring_point)
            )

            # Add a box around each measuring point section
            point_title = MeasuringPointTitle(
                measuring_point["name"],
                styles["Heading3"],
                analysis_type=analysis_type,
                analysed_entity_label=analysed_entity_label,
            )
            self.story.append(point_title)

            # Create info box with metadata
            info_items = []

            # Analysis type row
            info_items.append(
                [
                    Paragraph(_("Analysis type"), styles["Heading4"]),
                    Paragraph(analysis_type_label, styles["Normal"]),
                ]
            )

            # Reference row (if available)
            if analysed_entity_label:
                info_items.append(
                    [
                        Paragraph(_("Reference"), styles["Heading4"]),
                        Paragraph(analysed_entity_label, styles["Normal"]),
                    ]
                )

            # Apply better styling to info table
            info_table = Table(info_items, colWidths=[inch, 3 * inch], hAlign="LEFT")
            info_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                        ("BACKGROUND", (0, 0), (0, -1), BACKGROUND_COLOR),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )

            # Main content table structure (info + image if available)
            content_cols = []
            content_cols.append([info_table])

            if measuring_point["name"] in measuring_point_images:
                # Get image with enhanced styling
                img = generate_image_with_points(
                    measuring_point, measuring_point_images, temp_dir
                )
                img.borderColor = DEFAULT_BORDER_COLOR
                img.borderWidth = DEFAULT_BORDER_WIDTH
                img.borderPadding = DEFAULT_IMAGE_PADDING

                content_cols.append([img])

                # Two columns for layout with image
                col_widths = ["40%", "60%"]
            else:
                # One column layout without image
                col_widths = ["100%"]

            # Create main content table
            main_table = Table(
                [content_cols],
                colWidths=col_widths,
                hAlign="LEFT",  # Explicitly set horizontal alignment to left
                spaceBefore=6,
                spaceAfter=6,
            )

            # Create style list
            style_commands = [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ]

            # Add alignment for image column if it exists
            if len(content_cols) > 1:
                style_commands.append(("ALIGN", (1, 0), (1, 0), "CENTER"))

            main_table.setStyle(TableStyle(style_commands))

            self.story.append(main_table)

            # Add measuring point comments with styling
            self._add_point_comments(measuring_point["comments"])

            # Add a nice separator between measuring points
            self.story.append(
                HRFlowable(
                    width="100%",
                    thickness=1,
                    lineCap="round",
                    color=LIGHT_GRAY,
                    spaceBefore=0.3 * inch,
                    spaceAfter=0.5 * inch,
                )
            )

    def _add_point_comments(self, comments: str):
        """Add comments for a measuring point with markdown support"""
        self.story.append(Paragraph(_("Comments"), styles["Heading4"]))

        if not comments:
            self.story.append(Paragraph("-", styles["Normal"]))
            return

        # Add markdown-rendered paragraphs
        paragraphs = render_markdown_to_paragraphs(comments, styles)

        # Create a container for the comments with a light background
        comment_container = []
        comment_container.extend(paragraphs)

        # Create a table to hold the comments with styling
        comments_table = Table(
            [[p] for p in comment_container],
            colWidths=["100%"],
            hAlign="LEFT",  # Explicitly set horizontal alignment to left
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), BACKGROUND_COLOR),
                    ("BOX", (0, 0), (0, -1), 0.5, LIGHT_GRAY),
                    ("LEFTPADDING", (0, 0), (0, -1), 10),
                    ("RIGHTPADDING", (0, 0), (0, -1), 10),
                    ("TOPPADDING", (0, 0), (0, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (0, -1), 5),
                ]
            ),
        )

        self.story.append(comments_table)

    def _get_analysis_info(self, measuring_point: MeasuringPoint):
        """Extract analysis type information from a measuring point"""
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


def create_pdf(
    path: str,
    run: Run,
    run_methods: list["MethodDTO"],
    measuring_points: list[MeasuringPoint],
    images: list[NotebookImage],
):
    """
    Create a PDF document containing run information, experimental conditions,
    measuring points and images
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        context: PDFContext = {
            "run": run,
            "run_methods": run_methods,
            "measuring_points": measuring_points,
            "images": images,
            "temp_dir": temp_dir,
        }

        generator = PDFGenerator(context)
        generator.create_pdf(path)
