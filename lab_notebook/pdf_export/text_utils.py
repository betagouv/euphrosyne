import re
from typing import Dict, List

import markdown
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph

# Regex for basic markdown parsing if full markdown conversion isn't available
BOLD_PATTERN = re.compile(r"\*\*(.*?)\*\*|__(.*?)__")
ITALIC_PATTERN = re.compile(r"\*(.*?)\*|_(.*?)_")
LIST_ITEM_PATTERN = re.compile(r"^\s*[-*]\s+(.*?)$", re.MULTILINE)
HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.*?)$", re.MULTILINE)
LINKS_PATTERN = re.compile(r"\[(.*?)\]\((.*?)\)")


def markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML"""
    return markdown.markdown(text)


def split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs at blank lines"""
    if not text:
        return []

    paragraphs = []
    current_paragraph: list[str] = []

    for line in text.splitlines():
        if not line.strip() and current_paragraph:
            paragraphs.append("\n".join(current_paragraph))
            current_paragraph = []
        elif line.strip():
            current_paragraph.append(line)

    # Don't forget the last paragraph
    if current_paragraph:
        paragraphs.append("\n".join(current_paragraph))

    return paragraphs


def render_markdown_to_paragraphs(
    text: str, styles: Dict[str, ParagraphStyle]
) -> List[Flowable]:
    """
    Convert markdown text to a list of reportlab Paragraph objects
    with proper styling
    """
    if not text:
        return [Paragraph("-", styles["Normal"])]

    try:
        # Try to use markdown library for conversion
        html = markdown_to_html(text)

        # Split HTML by paragraph tags
        paragraph_texts = re.split(r"</?p>", html)

        # Filter out empty strings and convert to reportlab paragraphs
        paragraphs = []
        for p in paragraph_texts:
            if p.strip():
                paragraphs.append(Paragraph(p, styles["Normal"]))

        if paragraphs:
            return paragraphs

        # Fallback in case markdown produced unexpected output
        return [Paragraph(text, styles["Normal"])]

    except (ImportError, Exception):
        # Fallback to basic markdown parsing if markdown library fails
        return parse_basic_markdown(text, styles)


def parse_basic_markdown(
    text: str, styles: Dict[str, ParagraphStyle]
) -> List[Flowable]:
    """Simple markdown parser for basic formatting"""
    paragraphs = split_into_paragraphs(text)

    result = []
    for p in paragraphs:
        # Check if it's a header
        header_match = HEADER_PATTERN.match(p)
        if header_match:
            level = len(header_match.group(1))
            content = header_match.group(2)
            style_name = f"Heading{level}" if level <= 6 else "Heading6"
            if style_name in styles:
                result.append(Paragraph(content, styles[style_name]))
                continue

        # Check if it's a list item
        if LIST_ITEM_PATTERN.match(p):
            list_content = LIST_ITEM_PATTERN.sub(r"• \1", p)
            result.append(Paragraph(list_content, styles["Normal"]))
            continue

        # Process inline formatting
        p = BOLD_PATTERN.sub(r"<b>\1\2</b>", p)
        p = ITALIC_PATTERN.sub(r"<i>\1\2</i>", p)
        p = LINKS_PATTERN.sub(r'<a href="\2">\1</a>', p)

        result.append(Paragraph(p, styles["Normal"]))

    return result if result else [Paragraph(text, styles["Normal"])]
