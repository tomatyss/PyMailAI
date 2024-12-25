"""Email agent for AI-powered email processing."""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional, Union, cast

from pymailai.base_client import BaseEmailClient
from pymailai.client import EmailClient
from pymailai.config import EmailConfig
from pymailai.message import EmailData

logger = logging.getLogger(__name__)

# Type alias for message handler
MessageHandler = Callable[[EmailData], Coroutine[Any, Any, Optional[EmailData]]]


class EmailAgent:
    """Process incoming emails and generate responses using AI."""

    def __init__(
        self,
        config_or_client: Union[EmailConfig, BaseEmailClient],
        message_handler: Optional[MessageHandler] = None,
    ):
        """Initialize the email agent.

        Args:
            config_or_client: Either EmailConfig for IMAP/SMTP or a BaseEmailClient instance
            message_handler: Optional async callback for custom message processing
        """
        self.config = (
            config_or_client if isinstance(config_or_client, EmailConfig) else None
        )
        self.message_handler = message_handler
        self._client = (
            None if isinstance(config_or_client, EmailConfig) else config_or_client
        )
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def process_message(self, message: EmailData) -> Optional[EmailData]:
        """Process an incoming email message.

        This method can be overridden to implement custom processing logic.
        By default, it calls the message_handler if one was provided.

        Args:
            message: The incoming email message to process

        Returns:
            Optional response message to send
        """
        if self.message_handler:
            return await self.message_handler(message)
        return None

    async def _check_messages(self) -> None:
        """Poll for new messages and process them."""
        if not self._client:
            logger.error("Email client not initialized")
            return

        try:
            # Process messages as they come in
            async for message in self._client.fetch_new_messages():
                try:
                    # Process the message
                    response = await self.process_message(message)

                    # Mark original message as read
                    await self._client.mark_as_read(message.message_id)

                    # Send response if one was generated
                    if response and self._client:
                        await self._client.send_message(response)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Still mark as read to avoid reprocessing
                    if self._client:
                        await self._client.mark_as_read(message.message_id)

        except Exception as e:
            logger.error(f"Error fetching messages: {e}", exc_info=True)

    async def _run(self) -> None:
        """Run loop for the email agent."""
        if not self._client and self.config:
            self._client = cast(BaseEmailClient, EmailClient(self.config))

        try:
            if not self._client:
                raise RuntimeError("Email client not initialized")

            async with self._client:
                while self._running:
                    await self._check_messages()
                    # Use config interval if available, otherwise default to 60 seconds
                    await asyncio.sleep(
                        self.config.check_interval if self.config else 60
                    )
        finally:
            self._client = None

    async def start(self) -> None:
        """Start the email agent."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Email agent started")

    async def stop(self) -> None:
        """Stop the email agent."""
        if not self._running:
            return

        self._running = False
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass  # Task was cancelled, which is expected
            self._task = None
        logger.info("Email agent stopped")

    async def __aenter__(self) -> "EmailAgent":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
