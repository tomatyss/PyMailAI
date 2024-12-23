"""Comprehensive tests for EmailClient class."""

from unittest.mock import AsyncMock, patch

import pytest

from pymailai.client import EmailClient
from pymailai.config import EmailConfig
from pymailai.message import EmailData


@pytest.fixture
def email_config():
    """Create a test email configuration."""
    return EmailConfig(
        email="test@example.com",
        password="password",
        imap_server="imap.example.com",
        smtp_server="smtp.example.com",
        folder="INBOX",
        check_interval=60,
    )


@pytest.fixture
def test_message():
    """Create a test email message."""
    return EmailData(
        message_id="<test123@example.com>",
        subject="Test Subject",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
        cc_addresses=[],
        body_text="Test message",
        body_html=None,
        timestamp=None,
    )


@pytest.mark.asyncio
async def test_client_initialization(email_config):
    """Test EmailClient initialization."""
    client = EmailClient(email_config)
    assert client.config == email_config
    assert client._imap is None
    assert client._smtp is None


@pytest.mark.asyncio
async def test_connect_imap_smtp(email_config):
    """Test connecting to IMAP and SMTP servers."""
    client = EmailClient(email_config)

    # Mock IMAP
    mock_imap = AsyncMock()
    mock_imap.wait_hello_from_server = AsyncMock()
    mock_imap.login = AsyncMock()
    mock_imap.select = AsyncMock()

    # Mock SMTP
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()

    with patch('aioimaplib.IMAP4_SSL', return_value=mock_imap), \
            patch('aiosmtplib.SMTP', return_value=mock_smtp):
        await client.connect()

        # Verify IMAP connection
        mock_imap.wait_hello_from_server.assert_called_once()
        mock_imap.login.assert_called_once_with(email_config.email, email_config.password)
        mock_imap.select.assert_called_once_with(email_config.folder)

        # Verify SMTP connection
        mock_smtp.connect.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with(email_config.email, email_config.password)


@pytest.mark.asyncio
async def test_connect_smtp_ssl(email_config):
    """Test connecting to SMTP with SSL (port 465)."""
    email_config.smtp_port = 465
    client = EmailClient(email_config)

    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.login = AsyncMock()

    with patch('aioimaplib.IMAP4_SSL', return_value=AsyncMock()), \
            patch('aiosmtplib.SMTP', return_value=mock_smtp):
        await client.connect()

        # Verify SSL was used
        assert not mock_smtp.starttls.called


@pytest.mark.asyncio
async def test_connect_smtp_no_tls(email_config):
    """Test connecting to SMTP without TLS."""
    # Use port 25 since port 587 always requires TLS
    email_config.smtp_port = 25
    email_config.tls = False
    client = EmailClient(email_config)

    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.login = AsyncMock()

    with patch('aioimaplib.IMAP4_SSL', return_value=AsyncMock()), \
            patch('aiosmtplib.SMTP', return_value=mock_smtp):
        await client.connect()

        # Verify TLS was not used with port 25
        assert not mock_smtp.starttls.called


@pytest.mark.asyncio
async def test_fetch_new_messages_simple_format(email_config):
    """Test fetching new messages with simple IMAP response format."""
    client = EmailClient(email_config)
    client._imap = AsyncMock()

    # Mock IMAP search and fetch responses - exact format from production
    message_data = [
        b'1 FETCH (FLAGS (\\Seen) RFC822 {100}',
        bytearray(b'From: sender@example.com\r\nTo: recipient@example.com\r\nSubject: Test\r\n\r\nTest body'),
        b')',
        b'Fetch completed (0.001 + 0.000 secs).'
    ]
    client._imap.search.return_value = (None, [b'1'])
    client._imap.fetch.return_value = (None, message_data)

    messages = []
    async for msg in client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 1
    assert isinstance(messages[0], EmailData)
    assert messages[0].body_text.strip() == "Test body"
    client._imap.search.assert_called_once_with('UNSEEN')



@pytest.mark.asyncio
async def test_fetch_messages_with_attachments(email_config):
    """Test fetching messages with attachments."""
    client = EmailClient(email_config)
    client._imap = AsyncMock()

    # Mock message with attachment - exact format from production
    message_data = [
        b'1 FETCH (FLAGS (\\Seen) RFC822 {500}',
        bytearray(
            b'From: sender@example.com\r\n'
            b'To: recipient@example.com\r\n'
            b'Subject: Test with attachment\r\n'
            b'Content-Type: multipart/mixed; boundary="boundary"\r\n'
            b'MIME-Version: 1.0\r\n'
            b'Message-ID: <test123@example.com>\r\n\r\n'
            b'--boundary\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'Test body\r\n'
            b'--boundary\r\n'
            b'Content-Type: text/plain; name="test.txt"\r\n'
            b'Content-Disposition: attachment; filename="test.txt"\r\n'
            b'Content-Transfer-Encoding: base64\r\n\r\n'
            b'QXR0YWNobWVudCBjb250ZW50\r\n'  # base64 encoded "Attachment content"
            b'--boundary--\r\n'
        ),
        b')',
        b'Fetch completed (0.001 + 0.000 secs).'
    ]
    client._imap.search.return_value = (None, [b'1'])
    client._imap.fetch.return_value = (None, message_data)

    messages = []
    async for msg in client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 1
    assert len(messages[0].attachments) == 1
    attachment = messages[0].attachments[0]
    assert attachment["filename"] == "test.txt"
    assert attachment["content_type"] == "text/plain"


@pytest.mark.asyncio
async def test_fetch_messages_error_handling(email_config):
    """Test error handling during message fetching."""
    client = EmailClient(email_config)
    client._imap = AsyncMock()

    # Mock IMAP error
    client._imap.fetch.side_effect = Exception("Fetch error")
    client._imap.search.return_value = (None, [b'1'])

    messages = []
    async for msg in client.fetch_new_messages():
        messages.append(msg)

    assert len(messages) == 0


@pytest.mark.asyncio
async def test_mark_as_read(email_config):
    """Test marking a message as read."""
    client = EmailClient(email_config)
    client._imap = AsyncMock()

    message_id = "<test123@example.com>"
    client._imap.search.return_value = (None, [b'1'])

    await client.mark_as_read(message_id)

    client._imap.search.assert_called_once_with(f'HEADER "Message-ID" "{message_id}"')
    client._imap.store.assert_called_once_with('1', '+FLAGS', '\\Seen')


@pytest.mark.asyncio
async def test_mark_as_read_error_handling(email_config):
    """Test error handling when marking messages as read."""
    client = EmailClient(email_config)
    client._imap = AsyncMock()

    # Mock IMAP error
    client._imap.store.side_effect = Exception("Store error")
    client._imap.search.return_value = (None, [b'1'])

    # Should not raise exception
    await client.mark_as_read("<test123@example.com>")


@pytest.mark.asyncio
async def test_send_message(email_config, test_message):
    """Test sending a message."""
    client = EmailClient(email_config)
    client._smtp = AsyncMock()

    await client.send_message(test_message)

    client._smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect(email_config):
    """Test disconnecting from email servers."""
    client = EmailClient(email_config)

    # Set up mocks
    mock_imap = AsyncMock()
    mock_smtp = AsyncMock()
    client._imap = mock_imap
    client._smtp = mock_smtp

    await client.disconnect()

    # Verify disconnection
    mock_imap.logout.assert_called_once()
    mock_smtp.quit.assert_called_once()
    assert client._imap is None
    assert client._smtp is None


@pytest.mark.asyncio
async def test_context_manager(email_config):
    """Test async context manager functionality."""
    client = EmailClient(email_config)

    # Mock connect and disconnect
    mock_connect = AsyncMock()
    mock_disconnect = AsyncMock()
    client.connect = mock_connect
    client.disconnect = mock_disconnect

    async with client:
        mock_connect.assert_called_once()
    mock_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_smtp_starttls_error_handling(email_config):
    """Test SMTP STARTTLS error handling."""
    client = EmailClient(email_config)

    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock(side_effect=Exception("STARTTLS failed"))
    mock_smtp.login = AsyncMock()

    with patch('aioimaplib.IMAP4_SSL', return_value=AsyncMock()), \
            patch('aiosmtplib.SMTP', return_value=mock_smtp), \
            pytest.raises(Exception):  # Should raise for port 587
        await client.connect()


@pytest.mark.asyncio
async def test_smtp_starttls_error_handling_port_25(email_config):
    """Test SMTP STARTTLS error handling for port 25."""
    email_config.smtp_port = 25
    client = EmailClient(email_config)

    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock(side_effect=Exception("STARTTLS failed"))
    mock_smtp.login = AsyncMock()

    with patch('aioimaplib.IMAP4_SSL', return_value=AsyncMock()), \
            patch('aiosmtplib.SMTP', return_value=mock_smtp):
        # Should not raise for port 25
        await client.connect()
