"""Tests for markdown conversion in EmailData."""
from email.message import EmailMessage

from pymailai.message import EmailData


def test_markdown_conversion_in_email():
    """Test that markdown in email body is converted to HTML."""
    email_data = EmailData(
        message_id="test-id",
        subject="Test Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="# Hello\n\nThis is a **test** with markdown.",
        body_html=None,
        timestamp=None,  # type: ignore
    )

    msg: EmailMessage = email_data.to_email_message()

    # Get the HTML content
    html_part = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_content()
                break

    assert html_part is not None
    assert "<h1>Hello</h1>" in html_part
    assert "<strong>test</strong>" in html_part


def test_markdown_code_block_conversion():
    """Test that code blocks in markdown are converted to HTML."""
    email_data = EmailData(
        message_id="test-id",
        subject="Test Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text=(
            "# Code Example\n\n"
            "```python\n"
            "def hello():\n"
            "    print('Hello, world!')\n"
            "```"
        ),
        body_html=None,
        timestamp=None,  # type: ignore
    )

    msg: EmailMessage = email_data.to_email_message()

    # Get the HTML content
    html_part = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_content()
                break

    assert html_part is not None
    assert "<h1>Code Example</h1>" in html_part
    assert 'class="codehilite"' in html_part
    assert '<pre' in html_part
    assert '<code' in html_part
    assert "Hello, world!" in html_part


def test_no_markdown_conversion_with_existing_html():
    """Test that no markdown conversion occurs when HTML content is provided."""
    existing_html = "<div>Existing HTML</div>"
    email_data = EmailData(
        message_id="test-id",
        subject="Test Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="# This should not be converted",
        body_html=existing_html,
        timestamp=None,  # type: ignore
    )

    msg: EmailMessage = email_data.to_email_message()

    # Get the HTML content
    html_part = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_part = part.get_content()
                break

    assert html_part.strip() == existing_html.strip()


def test_no_markdown_conversion_without_markers():
    """Test that no markdown conversion occurs when text has no markdown markers."""
    plain_text = "This is just plain text without any markdown."
    email_data = EmailData(
        message_id="test-id",
        subject="Test Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text=plain_text,
        body_html=None,
        timestamp=None,  # type: ignore
    )

    msg: EmailMessage = email_data.to_email_message()

    # Check if message is multipart (it shouldn't be)
    assert not msg.is_multipart()
    assert msg.get_content().strip() == plain_text.strip()
