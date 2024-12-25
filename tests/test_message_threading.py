"""Tests for email message threading functionality."""

from datetime import datetime
from pymailai.message import EmailData


def test_format_quoted_text():
    """Test that text is properly quoted with attribution and > characters."""
    timestamp = datetime(2024, 1, 1, 14, 30)  # Fixed timestamp for testing
    email = EmailData(
        message_id="test-id",
        subject="Test",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="Line 1\nLine 2\n\nLine 3",
        body_html=None,
        timestamp=timestamp
    )

    # Test basic quotation
    quoted = email._format_quoted_text("Hello\nWorld", level=1)
    expected = (
        "On Jan 01, 2024, at 02:30 PM, from@example.com wrote:\n"
        ">\n"
        "> Hello\n"
        "> World"
    )
    assert quoted == expected

    # Test multiple quotation levels
    quoted = email._format_quoted_text("Hello\nWorld", level=2)
    expected = (
        "On Jan 01, 2024, at 02:30 PM, from@example.com wrote:\n"
        ">>\n"
        ">> Hello\n"
        ">> World"
    )
    assert quoted == expected

    # Test empty lines
    quoted = email._format_quoted_text("Hello\n\nWorld", level=1)
    expected = (
        "On Jan 01, 2024, at 02:30 PM, from@example.com wrote:\n"
        ">\n"
        "> Hello\n"
        ">\n"
        "> World"
    )
    assert quoted == expected


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

    # Check reply formatting (using regex to match since timestamp will vary)
    import re
    assert re.match(
        r"Reply text\n\n"
        r"On .+, from@example\.com wrote:\n"
        r">\n"
        r"> Original message",
        reply.body_text
    )

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

    # First reply (using fixed timestamp for predictable testing)
    reply1 = EmailData(
        message_id="reply1-id",
        subject="Re: Original Subject",
        from_address="bob@example.com",
        to_addresses=["alice@example.com"],
        cc_addresses=[],
        body_text="First reply\n\nOn Jan 01, 2024, at 02:30 PM, alice@example.com wrote:\n>\n> Original message",
        body_html=None,
        timestamp=datetime(2024, 1, 1, 14, 35)  # 5 minutes after original
    )

    # Second reply (to the first reply)
    reply2 = reply1.create_reply("Second reply", quote_level=2)

    # Check nested reply formatting with regex
    assert re.match(
        r"Second reply\n\n"
        r"On .+, bob@example\.com wrote:\n"
        r">>\n"
        r">> First reply\n\n"
        r"On Jan 01, 2024, at 02:30 PM, alice@example\.com wrote:\n"
        r">>\n"
        r">> > Original message",
        reply2.body_text
    )


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
