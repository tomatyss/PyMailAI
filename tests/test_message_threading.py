"""Tests for email message threading functionality."""

import re
from datetime import datetime
from pymailai.message import EmailData


def test_reply_format():
    """Test that replies preserve the entire thread history."""
    timestamp = datetime(2024, 1, 1, 14, 30)  # Fixed timestamp for testing
    email = EmailData(
        message_id="test-id",
        subject="Test",
        from_address="from@example.com",
        to_addresses=["to@example.com"],
        cc_addresses=[],
        body_text="Original message with\nmultiple lines\n\nand paragraphs",
        body_html=None,
        timestamp=timestamp
    )

    reply = email.create_reply("New reply text")
    expected = (
        "New reply text\n\n"
        "> -------- Original Message --------\n"
        "> Subject: Test\n"
        "> Date: Jan 01, 2024, at 02:30 PM\n"
        "> From: from@example.com\n"
        ">\n"
        "> Original message with\n"
        "> multiple lines\n"
        ">\n"
        "> and paragraphs"
    )
    assert reply.body_text == expected
    # Verify from/to addresses are correctly swapped
    assert reply.from_address == "to@example.com"  # Bot's address
    assert reply.to_addresses == ["from@example.com"]  # Original sender


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
    assert reply.from_address == "to@example.com"  # Bot's address
    assert reply.to_addresses == ["from@example.com"]  # Reply goes to original sender
    assert reply.cc_addresses == ["cc@example.com"]  # Preserves CC


def test_nested_reply_threading():
    """Test that nested replies preserve the entire conversation history."""
    # Original message
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="alice@example.com",
        to_addresses=["bot@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime(2024, 1, 1, 14, 30)  # Fixed timestamp
    )

    # First reply (from bot to alice)
    reply1 = original.create_reply("First reply")
    reply1.timestamp = datetime(2024, 1, 1, 14, 35)
    assert reply1.from_address == "bot@example.com"
    assert reply1.to_addresses == ["alice@example.com"]

    # Second reply (from alice back to bot)
    reply1_from_alice = EmailData(
        message_id="reply1-id",
        subject="Re: Original Subject",
        from_address="alice@example.com",
        to_addresses=["bot@example.com"],
        cc_addresses=[],
        body_text=reply1.body_text,
        timestamp=datetime(2024, 1, 1, 14, 35),
        references=reply1.references,
        in_reply_to=reply1.message_id
    )

    # Bot's second reply
    reply2 = reply1_from_alice.create_reply("Second reply")
    reply2.timestamp = datetime(2024, 1, 1, 14, 40)
    assert reply2.from_address == "bot@example.com"
    assert reply2.to_addresses == ["alice@example.com"]

    # Verify the complete thread is preserved
    expected = (
        "Second reply\n\n"
        "> -------- Original Message --------\n"
        "> Subject: Re: Original Subject\n"
        "> Date: Jan 01, 2024, at 02:35 PM\n"
        "> From: alice@example.com\n"
        ">\n"
        "> First reply\n"
        ">\n"
        "> > -------- Original Message --------\n"
        "> > Subject: Original Subject\n"
        "> > Date: Jan 01, 2024, at 02:30 PM\n"
        "> > From: alice@example.com\n"
        "> >\n"
        "> > Original message"
    )
    assert reply2.body_text == expected


def test_reply_without_history():
    """Test reply creation without including message history."""
    original = EmailData(
        message_id="original-id",
        subject="Original Subject",
        from_address="from@example.com",
        to_addresses=["bot@example.com"],
        cc_addresses=[],
        body_text="Original message",
        body_html=None,
        timestamp=datetime.now()
    )

    reply = original.create_reply("Reply text", include_history=False)

    # Check that only reply text is included
    assert reply.body_text == "Reply text"
    # Check from/to addresses
    assert reply.from_address == "bot@example.com"
    assert reply.to_addresses == ["from@example.com"]
    # Check threading metadata is still preserved
    assert reply.in_reply_to == "original-id"
    assert reply.references == ["original-id"]


def test_preserve_thread_history():
    """Test preservation of complete email thread history."""
    # Original message
    original = EmailData(
        message_id="msg1",
        subject="Original Subject",
        from_address="alice@example.com",
        to_addresses=["bot@example.com"],
        cc_addresses=[],
        body_text="First message",
        body_html=None,
        timestamp=datetime(2024, 1, 1, 14, 30)
    )

    # First reply from bot
    reply1 = original.create_reply("Second message")
    reply1.message_id = "msg2"
    reply1.timestamp = datetime(2024, 1, 1, 14, 35)
    assert reply1.from_address == "bot@example.com"
    assert reply1.to_addresses == ["alice@example.com"]

    # Simulate alice's reply to bot
    reply1_from_alice = EmailData(
        message_id="msg2",
        subject="Re: Original Subject",
        from_address="alice@example.com",
        to_addresses=["bot@example.com"],
        cc_addresses=[],
        body_text=reply1.body_text,
        timestamp=datetime(2024, 1, 1, 14, 35),
        references=reply1.references,
        in_reply_to=reply1.message_id
    )

    # Bot's second reply
    reply2 = reply1_from_alice.create_reply("Third message")
    reply2.message_id = "msg3"
    reply2.timestamp = datetime(2024, 1, 1, 14, 40)
    assert reply2.from_address == "bot@example.com"
    assert reply2.to_addresses == ["alice@example.com"]

    # Verify the complete thread is preserved
    expected_pattern = (
        r"Third message\n\n"
        r"> -------- Original Message --------\n"
        r"> Subject: Re: Original Subject\n"
        r"> Date: Jan 01, 2024, at 02:35 PM\n"
        r"> From: alice@example\.com\n"
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


def test_reply_no_recipients():
    """Test that replying to a message with no recipients raises an error."""
    email = EmailData(
        message_id="test-id",
        subject="Test",
        from_address="from@example.com",
        to_addresses=[],  # Empty recipients list
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now()
    )

    try:
        email.create_reply("Reply text")
        assert False, "Expected ValueError for message with no recipients"
    except ValueError as e:
        assert str(e) == "Cannot create reply: original message has no recipients"
