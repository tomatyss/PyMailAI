"""Tests for email message threading functionality."""

from datetime import datetime
from pymailai.message import EmailData


def test_format_quoted_text():
    """Test that text is properly quoted with > characters."""
    email = EmailData(
        message_id="test-id",
        subject="Test",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="Line 1\nLine 2\n\nLine 3",
        body_html=None,
        timestamp=datetime.now()
    )

    # Test basic quotation
    quoted = email._format_quoted_text("Hello\nWorld", level=1)
    assert quoted == "> Hello\n> World"

    # Test multiple quotation levels
    quoted = email._format_quoted_text("Hello\nWorld", level=2)
    assert quoted == ">> Hello\n>> World"

    # Test empty lines
    quoted = email._format_quoted_text("Hello\n\nWorld", level=1)
    assert quoted == "> Hello\n>\n> World"


def test_create_reply():
    """Test reply creation with proper threading fields."""
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=["cc@example.com"],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now(),
        references=["prev-id"]
    )

    reply = original.create_reply("Reply text")

    # Check threading fields
    assert reply.in_reply_to == "original-id"
    assert reply.references == ["prev-id", "original-id"]

    # Check reply formatting
    assert reply.body_text == "Reply text\n\n> Original message"

    # Check other fields
    assert reply.subject == "Re: Original Subject"
    assert reply.to_addresses == ["from@example.com"]  # Reply goes to original sender
    assert reply.cc_addresses == ["cc@example.com"]  # Preserves CC


def test_nested_reply_quotation():
    """Test increasing quotation levels in nested replies."""
    # Original message
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="alice@example.com",
        to_addresses=["bob@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now()
    )

    # First reply
    reply1 = original.create_reply("First reply")
    assert reply1.body_text == "First reply\n\n> Original message"

    # Second reply (to the first reply)
    reply2 = reply1.create_reply("Second reply", quote_level=2)
    expected = (
        "Second reply\n\n"
        ">> First reply\n"
        ">>\n"
        ">> > Original message"
    )
    assert reply2.body_text == expected


def test_reply_without_history():
    """Test reply creation without including message history."""
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now()
    )

    reply = original.create_reply("Reply text", include_history=False)

    # Check that only reply text is included
    assert reply.body_text == "Reply text"

    # But threading metadata is still preserved
    assert reply.in_reply_to == "original-id"
    assert reply.references == ["original-id"]
