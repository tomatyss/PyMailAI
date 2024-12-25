"""Tests for email message data structures and utilities."""

from datetime import datetime
from email.message import EmailMessage
from unittest.mock import MagicMock

import pytest

from pymailai.message import EmailData


def create_email_message(
    subject="Test Subject",
    from_addr="sender@example.com",
    to_addrs="recipient@example.com",
    cc_addrs="cc@example.com",
    body_text="Test message",
    body_html=None,
    attachments=None,
    message_id="<test123@example.com>",
    references="<ref1@example.com> <ref2@example.com>",
    in_reply_to="<original@example.com>",
    date="Thu, 1 Jan 2024 12:00:00 +0000",
) -> EmailMessage:
    """Helper function to create test email messages."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addrs
    msg["Cc"] = cc_addrs
    msg["Message-ID"] = message_id
    msg["References"] = references
    msg["In-Reply-To"] = in_reply_to
    msg["Date"] = date

    if attachments:
        # Start with multipart/mixed for attachments
        msg.make_mixed()

        # Create multipart/alternative for content
        alt_part = EmailMessage()
        alt_part.make_alternative()
        alt_part.add_alternative(body_text, subtype="plain")
        if body_html:
            alt_part.add_alternative(body_html, subtype="html")
        msg.attach(alt_part)

        # Add attachments
        for attachment in attachments:
            msg.add_attachment(
                attachment["payload"],
                maintype=attachment["maintype"],
                subtype=attachment["subtype"],
                filename=attachment["filename"],
                disposition="attachment",  # Explicitly set disposition
            )
    else:
        if body_html:
            # Create multipart/alternative for HTML and text
            msg.make_alternative()
            msg.add_alternative(body_text, subtype="plain")
            msg.add_alternative(body_html, subtype="html")
        else:
            # Simple text-only message
            msg.set_content(body_text)

    return msg


def test_email_data_from_simple_message():
    """Test creating EmailData from a simple text-only message."""
    msg = create_email_message()
    email_data = EmailData.from_email_message(msg)

    assert email_data.message_id == "<test123@example.com>"
    assert email_data.subject == "Test Subject"
    assert email_data.from_address == "sender@example.com"
    assert email_data.to_addresses == ["recipient@example.com"]
    assert email_data.cc_addresses == ["cc@example.com"]
    assert email_data.body_text.rstrip() == "Test message"
    assert email_data.body_html is None
    assert isinstance(email_data.timestamp, datetime)
    assert email_data.references == ["<ref1@example.com>", "<ref2@example.com>"]
    assert email_data.in_reply_to == "<original@example.com>"
    assert email_data.attachments == []


def test_email_data_from_html_message():
    """Test creating EmailData from a message with HTML content."""
    html_content = "<html><body><p>Test message</p></body></html>"
    msg = create_email_message(body_text="Test message", body_html=html_content)
    email_data = EmailData.from_email_message(msg)

    assert email_data.body_text.rstrip() == "Test message"
    assert email_data.body_html.rstrip() == html_content


def test_email_data_from_message_with_attachments():
    """Test creating EmailData from a message with attachments."""
    attachments = [
        {
            "payload": b"test file content",
            "maintype": "text",
            "subtype": "plain",
            "filename": "test.txt",
        }
    ]
    msg = create_email_message(attachments=attachments)
    email_data = EmailData.from_email_message(msg)

    assert len(email_data.attachments) == 1
    attachment = email_data.attachments[0]
    assert attachment["filename"] == "test.txt"
    assert attachment["content_type"] == "text/plain"
    assert attachment["payload"] == b"test file content"


def test_email_data_to_simple_message():
    """Test converting EmailData to a simple text-only message."""
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=["cc@example.com"],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now(),
        references=["<ref1@example.com>", "<ref2@example.com>"],
        in_reply_to="<original@example.com>",
        attachments=None,
    )

    msg = email_data.to_email_message()

    assert msg["Subject"] == "Test Subject"
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "recipient@example.com"
    assert msg["Cc"] == "cc@example.com"
    assert msg["References"] == "<ref1@example.com> <ref2@example.com>"
    assert msg["In-Reply-To"] == "<original@example.com>"
    assert msg.get_content().rstrip() == "Test message"


def test_email_data_to_html_message():
    """Test converting EmailData to a message with HTML content."""
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html="<html><body><p>Test message</p></body></html>",
        timestamp=datetime.now(),
    )

    msg = email_data.to_email_message()

    # Should be multipart/alternative
    assert msg.is_multipart()
    parts = list(msg.iter_parts())
    assert len(parts) == 2
    assert parts[0].get_content_type() == "text/plain"
    assert parts[1].get_content_type() == "text/html"


def test_email_data_to_message_with_attachments():
    """Test converting EmailData to a message with attachments."""
    attachments = [
        {
            "filename": "test.txt",
            "content_type": "text/plain",
            "payload": b"test file content",
        }
    ]
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now(),
        attachments=attachments,
    )

    msg = email_data.to_email_message()

    # Should be multipart/mixed
    assert msg.is_multipart()
    parts = list(msg.iter_parts())
    assert len(parts) == 2
    assert parts[0].get_content_type() == "text/plain"
    assert parts[1].get_content_type() == "text/plain"
    assert parts[1].get_filename() == "test.txt"


def test_email_data_to_html_message_with_attachments():
    """Test converting EmailData to a message with HTML and attachments."""
    attachments = [
        {
            "filename": "test.txt",
            "content_type": "text/plain",
            "payload": b"test file content",
        }
    ]
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html="<html><body><p>Test message</p></body></html>",
        timestamp=datetime.now(),
        attachments=attachments,
    )

    msg = email_data.to_email_message()

    # Should be multipart/mixed with nested multipart/alternative
    assert msg.is_multipart()
    parts = list(msg.iter_parts())
    assert len(parts) == 2

    # First part should be multipart/alternative
    assert parts[0].is_multipart()
    alt_parts = list(parts[0].iter_parts())
    assert len(alt_parts) == 2
    assert alt_parts[0].get_content_type() == "text/plain"
    assert alt_parts[1].get_content_type() == "text/html"

    # Second part should be the attachment
    assert parts[1].get_content_type() == "text/plain"
    assert parts[1].get_filename() == "test.txt"


def test_email_data_missing_fields():
    """Test handling of missing fields in email message."""
    msg = EmailMessage()
    msg.set_content("")  # Set empty content to avoid NoneType error
    email_data = EmailData.from_email_message(msg)

    assert email_data.message_id == ""
    assert email_data.subject == ""
    assert email_data.from_address == ""
    assert email_data.to_addresses == []
    assert email_data.cc_addresses == []
    assert email_data.body_text.strip() == ""
    assert email_data.body_html is None
    assert isinstance(email_data.timestamp, datetime)
    assert email_data.references == []
    assert email_data.in_reply_to is None
    assert email_data.attachments == []


def test_email_data_invalid_date():
    """Test handling of invalid date in email message."""
    msg = create_email_message(date="Invalid Date")
    email_data = EmailData.from_email_message(msg)

    # Should use a valid timestamp for invalid dates
    assert isinstance(email_data.timestamp, datetime)


def test_email_data_string_references():
    """Test handling of string references in EmailData initialization."""
    # Test with space-separated reference string
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now(),
        references="<ref1@example.com> <ref2@example.com>",
    )
    assert email_data.references == ["<ref1@example.com>", "<ref2@example.com>"]

    # Test with single reference string
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now(),
        references="<ref1@example.com>",
    )
    assert email_data.references == ["<ref1@example.com>"]

    # Test with empty string
    email_data = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now(),
        references="",
    )
    assert email_data.references == []


def test_email_data_invalid_references():
    """Test handling of invalid references type."""
    with pytest.raises(ValueError, match="References must be None, string, or list"):
        EmailData(
            message_id="<test123@example.com>",
            subject="Test Subject",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            cc_addresses=[],
            body_text="Test message",
            body_html=None,
            timestamp=datetime.now(),
            references=123,  # Invalid type
        )


def test_create_reply_with_string_references():
    """Test creating reply when original message has string references."""
    # Test with space-separated reference string
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references="<ref1@example.com> <ref2@example.com>",
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<ref1@example.com>", "<ref2@example.com>", "<test123@example.com>"]

    # Test with single reference string
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references="<ref1@example.com>",
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<ref1@example.com>", "<test123@example.com>"]

    # Test with empty string references
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references="",
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<test123@example.com>"]


def test_create_reply_with_list_references():
    """Test creating reply when original message has list references."""
    # Test with multiple references
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=["<ref1@example.com>", "<ref2@example.com>"],
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<ref1@example.com>", "<ref2@example.com>", "<test123@example.com>"]

    # Test with single reference
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=["<ref1@example.com>"],
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<ref1@example.com>", "<test123@example.com>"]

    # Test with empty list references
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=[],
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<test123@example.com>"]


def test_create_reply_with_none_references():
    """Test creating reply when original message has None references."""
    original = EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=None,
    )
    reply = original.create_reply("Reply text")
    assert reply.references == ["<test123@example.com>"]


def test_create_reply_chain():
    """Test creating a chain of replies to ensure references are properly maintained."""
    # First message
    original = EmailData(
        message_id="<original@example.com>",
        subject="Original Subject",
        from_address="sender1@example.com",
        to_addresses=["recipient1@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=None,
    )

    # First reply
    reply1 = original.create_reply("First reply")
    reply1.message_id = "<reply1@example.com>"  # Simulate server setting message ID
    assert reply1.references == ["<original@example.com>"]

    # Second reply
    reply2 = reply1.create_reply("Second reply")
    reply2.message_id = "<reply2@example.com>"  # Simulate server setting message ID
    assert reply2.references == ["<original@example.com>", "<reply1@example.com>"]

    # Third reply
    reply3 = reply2.create_reply("Third reply")
    reply3.message_id = "<reply3@example.com>"  # Simulate server setting message ID
    assert reply3.references == ["<original@example.com>", "<reply1@example.com>", "<reply2@example.com>"]
