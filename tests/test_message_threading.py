"""Tests for email message threading functionality."""

import re
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
        "> -------- Original Message --------\n"
        "> Subject: Test\n"
        "> Date: Jan 01, 2024, at 02:30 PM\n"
        "> From: from@example.com\n"
        ">\n"
        "> Hello\n"
        "> World"
    )
    assert quoted == expected

    # Test multiple quotation levels
    quoted = email._format_quoted_text("Hello\nWorld", level=2)
    expected = (
        ">> -------- Original Message --------\n"
        ">> Subject: Test\n"
        ">> Date: Jan 01, 2024, at 02:30 PM\n"
        ">> From: from@example.com\n"
        ">>\n"
        ">> Hello\n"
        ">> World"
    )
    assert quoted == expected

    # Test empty lines
    quoted = email._format_quoted_text("Hello\n\nWorld", level=1)
    expected = (
        "> -------- Original Message --------\n"
        "> Subject: Test\n"
        "> Date: Jan 01, 2024, at 02:30 PM\n"
        "> From: from@example.com\n"
        ">\n"
        "> Hello\n"
        ">\n"
        "> World"
    )
    assert quoted == expected

    # Test handling of existing quotes
    quoted = email._format_quoted_text(
        "Hello\n> Existing quote\n>> Nested quote", level=1
    )
    expected = (
        "> -------- Original Message --------\n"
        "> Subject: Test\n"
        "> Date: Jan 01, 2024, at 02:30 PM\n"
        "> From: from@example.com\n"
        ">\n"
        "> Hello\n"
        "> > Existing quote\n"
        "> >> Nested quote"
    )
    assert quoted == expected

    # Test handling of alternative quote formats
    quoted = email._format_quoted_text(
        "Hello\nOn Jan 1, 2024 someone@email.com wrote:\n> Previous text", level=1
    )
    expected = (
        "> -------- Original Message --------\n"
        "> Subject: Test\n"
        "> Date: Jan 01, 2024, at 02:30 PM\n"
        "> From: from@example.com\n"
        ">\n"
        "> Hello\n"
        "> On Jan 1, 2024 someone@email.com wrote:\n"
        "> > Previous text"
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
    pattern = (
        r"Reply text\n\n"
        r"> -------- Original Message --------\n"
        r"> Subject: Original Subject\n"
        r"> Date: [A-Z][a-z]{2} \d{2}, \d{4}, at \d{2}:\d{2} [AP]M\n"
        r"> From: from@example\.com\n"
        r">\n"
        r"> Original message"
    )
    assert re.match(pattern, reply.body_text), f"Expected pattern not found in:\n{reply.body_text}"

    # Check other fields
    assert reply.subject == "Re: Original Subject"
    assert reply.to_addresses == ["from@example.com"]  # Reply goes to original sender
    assert reply.cc_addresses == ["cc@example.com"]  # Preserves CC


def test_nested_reply_quotation():
    """Test increasing quotation levels in nested replies."""
    # Original message with fixed timestamp
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="alice@example.com",
        to_addresses=["bob@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime(2024, 1, 1, 14, 30)  # Fixed timestamp
    )

    # First reply (with proper from_address and fixed timestamp)
    reply1 = original.create_reply("First reply")
    reply1.from_address = "bob@example.com"  # Set the sender
    reply1.timestamp = datetime(2024, 1, 1, 14, 35)  # 5 minutes after original

    # Second reply (to the first reply)
    reply2 = reply1.create_reply("Second reply")
    reply2.from_address = "alice@example.com"  # Set the sender
    reply2.timestamp = datetime(2024, 1, 1, 14, 40)  # 5 minutes after reply1

    # Check nested reply formatting with regex
    pattern = (
        r"Second reply\n\n"
        r"> -------- Original Message --------\n"
        r"> Subject: Re: Original Subject\n"
        r"> Date: [A-Z][a-z]{2} \d{2}, \d{4}, at \d{2}:\d{2} [AP]M\n"
        r"> From: bob@example\.com\n"
        r">\n"
        r"> First reply\n"
        r">\n"
        r"> > -------- Original Message --------\n"
        r"> > Subject: Original Subject\n"
        r"> > Date: [A-Z][a-z]{2} \d{2}, \d{4}, at \d{2}:\d{2} [AP]M\n"
        r"> > From: alice@example\.com\n"
        r"> >\n"
        r"> > Original message"
    )
    assert re.match(pattern, reply2.body_text), f"Expected pattern not found in:\n{reply2.body_text}"


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


def test_preserve_thread_history():
    """Test preservation of complete email thread history."""
    # Original message
    original = EmailData(
        message_id="msg1",
        subject="Original Subject",
        from_address="alice@example.com",
        to_addresses=["bob@example.com"],
        cc_addresses=[],
        body_text="First message",
        body_html=None,
        timestamp=datetime(2024, 1, 1, 14, 30)
    )

    # First reply with quoted original
    reply1 = original.create_reply("Second message")
    reply1.message_id = "msg2"
    reply1.from_address = "bob@example.com"
    reply1.timestamp = datetime(2024, 1, 1, 14, 35)

    # Second reply should preserve both previous messages
    reply2 = reply1.create_reply("Third message")
    reply2.message_id = "msg3"
    reply2.from_address = "alice@example.com"
    reply2.timestamp = datetime(2024, 1, 1, 14, 40)

    # Verify the complete thread is preserved
    expected_pattern = (
        r"Third message\n\n"
        r"> -------- Original Message --------\n"
        r"> Subject: Re: Original Subject\n"
        r"> Date: Jan 01, 2024, at 02:35 PM\n"
        r"> From: bob@example\.com\n"
        r">\n"
        r"> Second message\n"
        r">\n"
        r"> > -------- Original Message --------\n"
        r"> > Subject: Original Subject\n"
        r"> > Date: Jan 01, 2024, at 02:30 PM\n"
        r"> > From: alice@example\.com\n"
        r"> >\n"
        r"> > First message"
    )

    assert re.match(expected_pattern, reply2.body_text), f"Expected pattern not found in:\n{reply2.body_text}"

    # Verify threading metadata
    assert reply2.in_reply_to == "msg2"
    assert reply2.references == ["msg1", "msg2"]
