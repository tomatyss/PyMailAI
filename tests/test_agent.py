"""Tests for the EmailAgent class."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pymailai.agent import EmailAgent
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


class AsyncIteratorMock:
    """Helper class to create async iterators for testing."""
    def __init__(self, items):
        self.items = items.copy()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self.items.pop(0)
        except IndexError:
            raise StopAsyncIteration


@pytest.mark.asyncio
async def test_agent_initialization(email_config):
    """Test EmailAgent initialization."""
    handler = AsyncMock()
    agent = EmailAgent(email_config, handler)

    assert agent.config == email_config
    assert agent.message_handler == handler
    assert agent._client is None
    assert not agent._running
    assert agent._task is None


@pytest.mark.asyncio
async def test_process_message_with_handler(email_config, test_message):
    """Test message processing with a custom handler."""
    expected_response = EmailData(
        message_id="<response123@example.com>",
        subject="Re: Test Subject",
        from_address="test@example.com",
        to_addresses=["sender@example.com"],
        cc_addresses=[],
        body_text="Response message",
        body_html=None,
        timestamp=None,
    )

    handler = AsyncMock(return_value=expected_response)
    agent = EmailAgent(email_config, handler)

    response = await agent.process_message(test_message)

    handler.assert_called_once_with(test_message)
    assert response == expected_response


@pytest.mark.asyncio
async def test_process_message_without_handler(email_config, test_message):
    """Test message processing without a handler."""
    agent = EmailAgent(email_config)
    response = await agent.process_message(test_message)
    assert response is None


@pytest.mark.asyncio
async def test_agent_start_stop(email_config):
    """Test starting and stopping the email agent."""
    agent = EmailAgent(email_config)

    # Mock the client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.fetch_new_messages = AsyncMock(return_value=AsyncIteratorMock([]))

    # Patch EmailClient to return our mock
    with patch('pymailai.agent.EmailClient', return_value=mock_client):
        # Start the agent
        await agent.start()
        assert agent._running
        assert agent._task is not None
        assert not agent._task.done()

        # Stop the agent
        await agent.stop()
        assert not agent._running
        assert agent._task is None


@pytest.mark.asyncio
async def test_check_messages(email_config, test_message):
    """Test checking for new messages."""
    handler = AsyncMock(return_value=test_message)
    agent = EmailAgent(email_config, handler)

    # Mock the email client
    mock_client = AsyncMock()

    # Create an async iterator for fetch_new_messages
    async def mock_fetch():
        yield test_message
    mock_client.fetch_new_messages = mock_fetch

    agent._client = mock_client

    # Run _check_messages
    await agent._check_messages()

    # Verify interactions
    handler.assert_called_once_with(test_message)
    mock_client.mark_as_read.assert_called_once_with(test_message.message_id)
    mock_client.send_message.assert_called_once_with(test_message)


@pytest.mark.asyncio
async def test_agent_context_manager(email_config):
    """Test async context manager functionality."""
    agent = EmailAgent(email_config)

    # Mock the client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.fetch_new_messages = AsyncMock(return_value=AsyncIteratorMock([]))

    # Patch EmailClient to return our mock
    with patch('pymailai.agent.EmailClient', return_value=mock_client):
        async with agent as ctx:
            assert ctx == agent
            assert agent._running
            assert agent._task is not None

        assert not agent._running
        assert agent._task is None


@pytest.mark.asyncio
async def test_check_messages_error_handling(email_config):
    """Test error handling during message checking."""
    agent = EmailAgent(email_config)

    # Mock client with an async iterator that raises an exception
    mock_client = AsyncMock()

    class ErrorIterator:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise Exception("Test error")

    mock_client.fetch_new_messages = lambda: ErrorIterator()
    agent._client = mock_client

    # Should not raise exception
    await agent._check_messages()


@pytest.mark.asyncio
async def test_message_processing_error_handling(email_config, test_message):
    """Test error handling during message processing."""
    handler = AsyncMock(side_effect=Exception("Processing error"))
    agent = EmailAgent(email_config, handler)

    # Mock the email client
    mock_client = AsyncMock()

    # Create an async iterator for fetch_new_messages
    async def mock_fetch():
        yield test_message
    mock_client.fetch_new_messages = mock_fetch

    agent._client = mock_client

    # Should not raise exception
    await agent._check_messages()

    # Verify message was marked as read despite processing error
    mock_client.mark_as_read.assert_called_once_with(test_message.message_id)

    # Verify send_message was not called due to handler error
    mock_client.send_message.assert_not_called()
