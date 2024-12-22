"""Tests for core PyMailAI functionality."""

import pytest
from email.message import EmailMessage
from datetime import datetime
from unittest.mock import patch

from pymailai.config import EmailConfig
from pymailai.message import EmailData


@pytest.fixture
def mock_email_validator():
    """Mock email validator to avoid real network calls."""
    with patch('email_validator.validate_email') as mock_validate:
        def validate_side_effect(email):
            if email == "not-an-email":
                from email_validator import EmailNotValidError
                raise EmailNotValidError("Invalid email format")
            return True
        mock_validate.side_effect = validate_side_effect
        yield mock_validate


def test_email_config_validation(mock_email_validator):
    """Test EmailConfig validation."""
    # Valid configuration
    config = EmailConfig(
        imap_server="imap.gmail.com",
        smtp_server="smtp.gmail.com",
        email="test@example.com",
        password="secret"
    )
    config.validate()  # Should not raise

    # Invalid email
    with pytest.raises(ValueError, match="Invalid email address"):
        config = EmailConfig(
            imap_server="imap.gmail.com",
            smtp_server="smtp.gmail.com",
            email="not-an-email",
            password="secret"
        )
        config.validate()

    # Missing password
    with pytest.raises(ValueError, match="Password cannot be empty"):
        config = EmailConfig(
            imap_server="imap.gmail.com",
            smtp_server="smtp.gmail.com",
            email="test@example.com",
            password=""
        )
        config.validate()

    # Missing servers
    with pytest.raises(ValueError, match="IMAP and SMTP servers must be specified"):
        config = EmailConfig(
            imap_server="",
            smtp_server="",
            email="test@example.com",
            password="secret"
        )
        config.validate()


def test_email_data_conversion():
    """Test EmailData conversion to/from EmailMessage."""
    # Create a test EmailMessage
    msg = EmailMessage()
    msg["Subject"] = "Test Subject"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Message-ID"] = "<123@example.com>"
    msg["Date"] = "Thu, 1 Jan 2023 12:00:00 +0000"
    msg.set_content("Test message body")

    # Convert to EmailData
    email_data = EmailData.from_email_message(msg)

    # Verify conversion
    assert email_data.subject == "Test Subject"
    assert email_data.from_address == "sender@example.com"
    assert email_data.to_addresses == ["recipient@example.com"]
    assert email_data.body_text.rstrip() == "Test message body"
    assert email_data.message_id == "<123@example.com>"

    # Convert back to EmailMessage
    new_msg = email_data.to_email_message()

    # Verify round-trip conversion
    assert new_msg["Subject"] == msg["Subject"]
    assert new_msg["From"] == msg["From"]
    assert new_msg["To"] == msg["To"]
    assert new_msg.get_content() == msg.get_content()


def test_email_data_multipart():
    """Test EmailData handling of multipart messages."""
    # Create a test multipart message
    msg = EmailMessage()
    msg["Subject"] = "Multipart Test"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Message-ID"] = "<123@example.com>"
    msg["Date"] = "Thu, 1 Jan 2023 12:00:00 +0000"

    # Add plain text and HTML content
    msg.make_alternative()  # First make alternative part
    msg.add_alternative("Plain text content", subtype="plain")
    msg.add_alternative("<p>HTML content</p>", subtype="html")

    # Convert to EmailData
    email_data = EmailData.from_email_message(msg)

    # Verify both parts were captured
    assert "Plain text content" in email_data.body_text
    assert "<p>HTML content</p>" in email_data.body_html

    # Convert back to EmailMessage
    new_msg = email_data.to_email_message()

    # Verify multipart structure is preserved
    assert new_msg.is_multipart()
    parts = list(new_msg.iter_parts())
    assert len(parts) == 2
    assert "Plain text content" in parts[0].get_content()
    assert "<p>HTML content</p>" in parts[1].get_content()
