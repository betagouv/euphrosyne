from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch, mm

# PDF configuration constants
PAGE_SIZE = A4
DEFAULT_MAX_IMAGE_WIDTH = 3 * inch
DEFAULT_MAX_IMAGE_HEIGHT = 3 * inch
IMAGES_PER_ROW = 2

# Color scheme
PRIMARY_COLOR = colors.HexColor("#2D52A8")  # Blue
SECONDARY_COLOR = colors.HexColor("#DB5461")  # Red
TEXT_COLOR = colors.HexColor("#333333")  # Dark gray
HEADING_COLOR = colors.HexColor("#1A315F")  # Dark blue
LIGHT_GRAY = colors.HexColor("#EDEDED")  # Light gray for separators
BACKGROUND_COLOR = colors.HexColor("#F9F9F9")  # Very light gray for backgrounds

# Get sample styles
base_styles = getSampleStyleSheet()

# Create a dictionary of custom styles
styles = {}

# Copy existing styles from sample
for style_name, style in base_styles.byName.items():
    styles[style_name] = style

# Document title style
styles["Title"] = ParagraphStyle(
    name="Title",
    parent=base_styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=HEADING_COLOR,
    alignment=TA_LEFT,
    spaceAfter=12,
)

# Main headings style
styles["Heading1"] = ParagraphStyle(
    name="Heading1",
    parent=base_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=HEADING_COLOR,
    alignment=TA_LEFT,
    spaceAfter=8,
    spaceBefore=20,
    borderColor=PRIMARY_COLOR,
    borderWidth=0,
    borderPadding=5,
    borderRadius=2,
)

# Section headings style
styles["Heading2"] = ParagraphStyle(
    name="Heading2",
    parent=base_styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    textColor=PRIMARY_COLOR,
    alignment=TA_LEFT,
    spaceAfter=8,
    spaceBefore=15,
)

# Sub-section headings style
styles["Heading3"] = ParagraphStyle(
    name="Heading3",
    parent=base_styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=HEADING_COLOR,
    alignment=TA_LEFT,
    spaceAfter=6,
    spaceBefore=12,
)

# Field headings style
styles["Heading4"] = ParagraphStyle(
    name="Heading4",
    parent=base_styles["Heading4"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=14,
    textColor=SECONDARY_COLOR,
    alignment=TA_LEFT,
    spaceAfter=3,
    spaceBefore=6,
)

# Normal text style
styles["Normal"] = ParagraphStyle(
    name="Normal",
    parent=base_styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=TEXT_COLOR,
    alignment=TA_LEFT,
    spaceAfter=8,
)

# Indented style for nested content
INDENTED_STYLE = ParagraphStyle(
    name="Indented",
    parent=styles["Normal"],
    leftIndent=10,
    textColor=TEXT_COLOR,
)

# Image caption style
CAPTION_STYLE = ParagraphStyle(
    name="Caption",
    parent=styles["Normal"],
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
    textColor=HEADING_COLOR,
)

# Table of contents styles
TOC_TITLE_STYLE = ParagraphStyle(
    name="TOCTitle",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    spaceBefore=20,
    spaceAfter=10,
)

TOC_ENTRY_STYLE = ParagraphStyle(
    name="TOCEntry",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    textColor=TEXT_COLOR,
)

# Page settings
PAGE_MARGIN = 2 * cm  # 2cm margins
PAGE_WIDTH, PAGE_HEIGHT = A4

# Image settings
DEFAULT_BORDER_COLOR = LIGHT_GRAY
DEFAULT_BORDER_WIDTH = 1
DEFAULT_IMAGE_PADDING = 5 * mm
