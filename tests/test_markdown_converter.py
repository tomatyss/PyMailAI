"""Tests for the markdown converter module."""
import pytest
from pymailai.markdown_converter import MarkdownConverter


def test_basic_markdown_conversion():
    """Test basic markdown to HTML conversion."""
    converter = MarkdownConverter()
    markdown_content = "# Hello\n\nThis is a **test**."
    expected_html = "<h1>Hello</h1>\n<p>This is a <strong>test</strong>.</p>"
    assert converter.convert(markdown_content).strip() == expected_html


def test_markdown_with_code():
    """Test markdown conversion with code blocks."""
    converter = MarkdownConverter()
    markdown_content = (
        "# Code Example\n\n"
        "```python\n"
        "def hello():\n"
        "    print('Hello, world!')\n"
        "```"
    )
    html = converter.convert(markdown_content)
    assert "<h1>Code Example</h1>" in html
    assert 'class="codehilite"' in html
    assert '<pre' in html
    assert '<code' in html
    assert "Hello, world!" in html  # Check for the content without worrying about exact HTML structure


def test_markdown_with_table():
    """Test markdown conversion with tables."""
    converter = MarkdownConverter()
    markdown_content = (
        "| Header 1 | Header 2 |\n"
        "|----------|----------|\n"
        "| Cell 1   | Cell 2   |"
    )
    html = converter.convert(markdown_content)
    assert "<table>" in html
    assert "<th>Header 1</th>" in html
    assert "<td>Cell 1</td>" in html


def test_custom_extensions():
    """Test markdown conversion with custom extensions."""
    converter = MarkdownConverter(extensions=['tables'])
    markdown_content = (
        "| Header 1 | Header 2 |\n"
        "|----------|----------|\n"
        "| Cell 1   | Cell 2   |"
    )
    html = converter.convert(markdown_content)
    assert "<table>" in html


def test_converter_reset():
    """Test resetting the markdown converter."""
    converter = MarkdownConverter()
    markdown_content = "# Test"
    converter.convert(markdown_content)
    converter.reset()
    assert converter.convert(markdown_content).strip() == "<h1>Test</h1>"
