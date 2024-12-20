"""Email agent for AI-powered email processing."""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

from pymailai.client import EmailClient
from pymailai.config import EmailConfig
from pymailai.message import EmailData

logger = logging.getLogger(__name__)

# Type alias for message handler
MessageHandler = Callable[[EmailData], Coroutine[Any, Any, Optional[EmailData]]]


class EmailAgent:
    """AI-powered email agent that processes incoming emails and generates responses."""

    def __init__(
        self,
        config: EmailConfig,
        message_handler: Optional[MessageHandler] = None
    ):
        """Initialize the email agent.
        
        Args:
            config: Email configuration settings
            message_handler: Optional async callback for custom message processing
        """
        self.config = config
        self.message_handler = message_handler
        self._client: Optional[EmailClient] = None
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
        """Check for new messages and process them."""
        try:
            async for message in self._client.fetch_new_messages():
                try:
                    # Process the message
                    response = await self.process_message(message)
                    
                    # Mark original message as read
                    await self._client.mark_as_read(message.message_id)
                    
                    # Send response if one was generated
                    if response:
                        await self._client.send_message(response)
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Error fetching messages: {e}", exc_info=True)

    async def _run(self) -> None:
        """Main run loop for the email agent."""
        self._client = EmailClient(self.config)
        
        try:
            async with self._client:
                while self._running:
                    await self._check_messages()
                    await asyncio.sleep(self.config.check_interval)
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
            await self._task
            self._task = None
        logger.info("Email agent stopped")

    async def __aenter__(self) -> "EmailAgent":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
