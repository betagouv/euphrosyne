from unittest import mock

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from lab_notebook.pdf_export.text_utils import (
    markdown_to_html,
    parse_basic_markdown,
    render_markdown_to_paragraphs,
    split_into_paragraphs,
)

# Get sample styles for testing
STYLES = getSampleStyleSheet()


def test_markdown_to_html():
    # Test basic markdown conversion
    md_text = "**Bold text** and *italic text*"
    html = markdown_to_html(md_text)
    assert "<strong>Bold text</strong>" in html
    assert "<em>italic text</em>" in html

    # Test with links
    md_text = "[Link text](https://example.com)"
    html = markdown_to_html(md_text)
    assert '<a href="https://example.com">Link text</a>' in html

    # Test with headers
    md_text = "# Heading 1\n## Heading 2"
    html = markdown_to_html(md_text)
    assert "<h1>Heading 1</h1>" in html
    assert "<h2>Heading 2</h2>" in html

    # Test with lists
    md_text = "- Item 1\n- Item 2"
    html = markdown_to_html(md_text)
    assert "<li>Item 1</li>" in html
    assert "<li>Item 2</li>" in html


def test_split_into_paragraphs():
    # Test with multiple paragraphs
    text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    paragraphs = split_into_paragraphs(text)
    assert len(paragraphs) == 3
    assert paragraphs[0] == "Paragraph 1"
    assert paragraphs[1] == "Paragraph 2"
    assert paragraphs[2] == "Paragraph 3"

    # Test with empty text
    # pylint: disable=use-implicit-booleaness-not-comparison)
    assert split_into_paragraphs("") == []

    # Test with single paragraph
    assert split_into_paragraphs("Single paragraph") == ["Single paragraph"]

    # Test with multi-line paragraphs
    text = "Line 1\nLine 2\n\nLine 3\nLine 4"
    paragraphs = split_into_paragraphs(text)
    assert len(paragraphs) == 2
    assert paragraphs[0] == "Line 1\nLine 2"
    assert paragraphs[1] == "Line 3\nLine 4"


def test_render_markdown_to_paragraphs():
    # Test with basic markdown
    md_text = "**Bold text** and *italic text*"
    paragraphs = render_markdown_to_paragraphs(md_text, STYLES)
    assert len(paragraphs) == 1
    assert isinstance(paragraphs[0], Paragraph)

    # Test with multiple paragraphs
    md_text = "Paragraph 1\n\nParagraph 2"
    paragraphs = render_markdown_to_paragraphs(md_text, STYLES)
    assert len(paragraphs) == 2
    assert all(isinstance(p, Paragraph) for p in paragraphs)

    # Test with empty text
    paragraphs = render_markdown_to_paragraphs("", STYLES)
    assert len(paragraphs) == 1
    assert isinstance(paragraphs[0], Paragraph)
    assert paragraphs[0].text == "-"

    # Test fallback when markdown module fails
    with mock.patch(
        "lab_notebook.pdf_export.text_utils.markdown_to_html", side_effect=ImportError
    ):
        paragraphs = render_markdown_to_paragraphs("Some text", STYLES)
        assert len(paragraphs) == 1
        assert isinstance(paragraphs[0], Paragraph)


def test_parse_basic_markdown():
    # Test basic formatting
    md_text = "**Bold text** and *italic text*"
    paragraphs = parse_basic_markdown(md_text, STYLES)
    assert len(paragraphs) == 1
    assert isinstance(paragraphs[0], Paragraph)
    assert "<b>Bold text</b>" in paragraphs[0].text
    assert "<i>italic text</i>" in paragraphs[0].text

    # Test headers
    md_text = "# Heading 1"
    paragraphs = parse_basic_markdown(md_text, STYLES)
    assert len(paragraphs) == 1
    assert isinstance(paragraphs[0], Paragraph)
    assert paragraphs[0].style.name == "Heading1"
    assert "Heading 1" in paragraphs[0].text

    # Test list items - note our implementation combines them into one paragraph
    md_text = "- Item 1\n- Item 2"
    paragraphs = parse_basic_markdown(md_text, STYLES)
    assert len(paragraphs) == 1
    assert isinstance(paragraphs[0], Paragraph)
    assert "• Item 1" in paragraphs[0].text
    assert "• Item 2" in paragraphs[0].text

    # Test links
    md_text = "[Link text](https://example.com)"
    paragraphs = parse_basic_markdown(md_text, STYLES)
    assert len(paragraphs) == 1
    assert '<a href="https://example.com">Link text</a>' in paragraphs[0].text
