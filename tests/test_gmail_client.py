"""Tests for GmailClient class."""

import base64
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pymailai.gmail_client import GmailClient
from pymailai.message import EmailData


@pytest.fixture
def mock_gmail_service():
    """Create a mock Gmail service."""
    mock_service = MagicMock()
    return mock_service


@pytest.fixture
def gmail_client(mock_gmail_service):
    """Create a GmailClient instance with mock service."""
    return GmailClient(mock_gmail_service)


@pytest.mark.asyncio
async def test_mark_as_read(gmail_client, mock_gmail_service):
    """Test marking a message as read."""
    message_id = "test_message_id"

    # Set up mock
    mock_modify = mock_gmail_service.users.return_value.messages.return_value.modify
    mock_modify.return_value.execute.return_value = {"id": message_id}

    # Call mark_as_read
    await gmail_client.mark_as_read(message_id)

    # Verify the API was called correctly
    mock_gmail_service.users.assert_called_once_with()
    mock_gmail_service.users().messages.assert_called_once_with()
    mock_modify.assert_called_once_with(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    )
    mock_modify.return_value.execute.assert_called_once()


@pytest.mark.asyncio
async def test_mark_as_read_error_handling(gmail_client, mock_gmail_service):
    """Test error handling when marking a message as read."""
    message_id = "test_message_id"

    # Set up mock to raise an exception
    mock_modify = mock_gmail_service.users.return_value.messages.return_value.modify
    mock_modify.return_value.execute.side_effect = Exception("API error")

    # Call mark_as_read - should not raise exception
    await gmail_client.mark_as_read(message_id)

    # Verify the API was called
    mock_modify.assert_called_once_with(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    )


@pytest.mark.asyncio
async def test_fetch_new_messages_single_part(gmail_client, mock_gmail_service):
    """Test fetching single part text message."""
    mock_list = mock_gmail_service.users.return_value.messages.return_value.list
    mock_get = mock_gmail_service.users.return_value.messages.return_value.get

    mock_list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}]
    }

    mock_get.return_value.execute.return_value = {
        "id": "msg1",
        "internalDate": "1706179200000",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Thu, 25 Jan 2024 10:00:00 +0000"}
            ],
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(b"Test message").decode()
            }
        }
    }

    messages = []
    async for msg in gmail_client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 1
    assert messages[0].body_text == "Test message"
    assert messages[0].body_html is None


@pytest.mark.asyncio
async def test_fetch_new_messages_multipart_alternative(gmail_client, mock_gmail_service):
    """Test fetching multipart/alternative message with text and HTML parts."""
    mock_list = mock_gmail_service.users.return_value.messages.return_value.list
    mock_get = mock_gmail_service.users.return_value.messages.return_value.get

    mock_list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}]
    }

    mock_get.return_value.execute.return_value = {
        "id": "msg1",
        "internalDate": "1706179200000",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Thu, 25 Jan 2024 10:00:00 +0000"}
            ],
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"Plain text").decode()
                    }
                },
                {
                    "mimeType": "text/html",
                    "body": {
                        "data": base64.urlsafe_b64encode(b"<p>HTML content</p>").decode()
                    }
                }
            ]
        }
    }

    messages = []
    async for msg in gmail_client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 1
    assert messages[0].body_text == "Plain text"
    assert messages[0].body_html == "<p>HTML content</p>"


@pytest.mark.asyncio
async def test_fetch_new_messages_multipart_mixed_nested(gmail_client, mock_gmail_service):
    """Test fetching multipart/mixed message with nested multipart/alternative."""
    mock_list = mock_gmail_service.users.return_value.messages.return_value.list
    mock_get = mock_gmail_service.users.return_value.messages.return_value.get

    mock_list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}]
    }

    mock_get.return_value.execute.return_value = {
        "id": "msg1",
        "internalDate": "1706179200000",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "recipient@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Thu, 25 Jan 2024 10:00:00 +0000"},
                {"name": "Message-ID", "value": "<test123@example.com>"}
            ],
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {
                                "data": base64.urlsafe_b64encode(b"""Hello!

Here's a test message with multiple sections:

- Section 1: Testing
- Section 2: Verification
- Section 3: Validation

Next steps:
1. Check plain text extraction
2. Verify HTML content
3. Confirm attachment handling

Best regards,
Test User""").decode()
                            }
                        },
                        {
                            "mimeType": "text/html",
                            "body": {
                                "data": base64.urlsafe_b64encode(b"""<div dir="ltr">Hello!<br><br>Here's a test message with multiple sections:<br><br>- Section 1: Testing<br>- Section 2: Verification<br>- Section 3: Validation<br><br>Next steps:<br>1. Check plain text extraction<br>2. Verify HTML content<br>3. Confirm attachment handling<br><br>Best regards,<br>Test User</div>""").decode()
                            }
                        }
                    ]
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "test.pdf",
                    "body": {
                        "attachmentId": "attachment123"
                    }
                }
            ]
        }
    }

    messages = []
    async for msg in gmail_client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 1
    assert messages[0].message_id == "msg1"
    assert messages[0].subject == "Test Subject"
    assert messages[0].from_address == "sender@example.com"
    assert messages[0].to_addresses == ["recipient@example.com"]

    # Verify both plain text and HTML content are extracted
    assert "Hello!" in messages[0].body_text
    assert "Section 1: Testing" in messages[0].body_text
    assert "Next steps:" in messages[0].body_text
    assert "Best regards," in messages[0].body_text

    assert "<div dir=\"ltr\">" in messages[0].body_html
    assert "Section 1: Testing" in messages[0].body_html
    assert "Next steps:" in messages[0].body_html
    assert "<br>Test User</div>" in messages[0].body_html


@pytest.mark.asyncio
async def test_fetch_new_messages_no_messages(gmail_client, mock_gmail_service):
    """Test fetching when there are no new messages."""
    # Set up mock to return no messages
    mock_list = mock_gmail_service.users.return_value.messages.return_value.list
    mock_list.return_value.execute.return_value = {}

    # Fetch messages
    messages = []
    async for msg in gmail_client.fetch_new_messages():
        messages.append(msg)

    # Verify no messages were returned
    assert len(messages) == 0

    # Verify API call
    mock_list.assert_called_once_with(userId="me", q="is:unread -in:chats")


@pytest.mark.asyncio
async def test_send_message(gmail_client, mock_gmail_service):
    """Test sending a message."""
    # Create test message
    message = EmailData(
        message_id="test123",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now()
    )

    # Set up mock
    mock_send = mock_gmail_service.users.return_value.messages.return_value.send
    mock_send.return_value.execute.return_value = {"id": "msg1"}

    # Send message
    await gmail_client.send_message(message)

    # Verify API calls
    mock_gmail_service.users.assert_called_once_with()
    mock_gmail_service.users().messages.assert_called_once_with()
    mock_send.assert_called_once()
    mock_send.return_value.execute.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_error_handling(gmail_client, mock_gmail_service):
    """Test error handling when sending a message."""
    # Create test message
    message = EmailData(
        message_id="test123",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=datetime.now()
    )

    # Set up mock to raise an exception
    mock_send = mock_gmail_service.users.return_value.messages.return_value.send
    mock_send.return_value.execute.side_effect = Exception("API error")

    # Send message - should raise exception
    with pytest.raises(Exception):
        await gmail_client.send_message(message)
