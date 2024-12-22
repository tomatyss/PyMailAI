"""Email client implementation."""

import email
import logging
from email.message import EmailMessage
from typing import AsyncGenerator, Optional

import aioimaplib
import aiosmtplib

from pymailai.config import EmailConfig
from pymailai.message import EmailData

logger = logging.getLogger(__name__)


class EmailClient:
    """Asynchronous email client for IMAP and SMTP operations."""

    def __init__(self, config: EmailConfig):
        """Initialize email client with configuration."""
        self.config = config
        self._imap: Optional[aioimaplib.IMAP4_SSL] = None
        self._smtp: Optional[aiosmtplib.SMTP] = None

    async def connect(self) -> None:
        """Establish connections to IMAP and SMTP servers."""
        # Connect to IMAP
        self._imap = aioimaplib.IMAP4_SSL(
            host=self.config.imap_server,
            port=self.config.imap_port,
            timeout=self.config.timeout,
        )
        await self._imap.wait_hello_from_server()
        logger.debug(
            "Connected to IMAP server %s:%s",
            self.config.imap_server,
            self.config.imap_port,
        )
        await self._imap.login(self.config.email, self.config.password)
        logger.debug("Logged in to IMAP server as %s", self.config.email)
        await self._imap.select(self.config.folder)
        logger.debug("Selected IMAP folder: %s", self.config.folder)

        # Connect to SMTP with appropriate security
        if self.config.smtp_port == 465:
            # Port 465 uses implicit SSL/TLS
            self._smtp = aiosmtplib.SMTP(
                hostname=self.config.smtp_server,
                port=self.config.smtp_port,
                timeout=self.config.timeout,
                use_tls=True,  # Immediate TLS for port 465
            )
            await self._smtp.connect()
            logger.debug(
                "Connected to SMTP server %s:%s with SSL/TLS",
                self.config.smtp_server,
                self.config.smtp_port,
            )
        else:
            # Ports 25 and 587 start unencrypted
            self._smtp = aiosmtplib.SMTP(
                hostname=self.config.smtp_server,
                port=self.config.smtp_port,
                timeout=self.config.timeout,
                use_tls=False,
            )
            await self._smtp.connect()
            logger.debug(
                "Connected to SMTP server %s:%s",
                self.config.smtp_server,
                self.config.smtp_port,
            )

            # Use STARTTLS if available (standard for port 587)
            if self.config.tls:
                try:
                    await self._smtp.starttls()
                except Exception as e:
                    if self.config.smtp_port == 587:
                        # STARTTLS is required for port 587
                        raise
                    # For other ports like 25, continue without TLS if it fails
                    logger.warning("STARTTLS failed: %s", e)
        await self._smtp.login(self.config.email, self.config.password)
        logger.debug("Logged in to SMTP server as %s", self.config.email)

    async def disconnect(self) -> None:
        """Close connections to email servers."""
        if self._imap:
            await self._imap.logout()
            logger.debug("Disconnected from IMAP server")
            self._imap = None
        if self._smtp:
            await self._smtp.quit()
            logger.debug("Disconnected from SMTP server")
            self._smtp = None

    async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
        """Fetch new unread messages from the IMAP server."""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")

        # Search for unread messages
        _, data = await self._imap.search("UNSEEN")
        message_numbers = data[0].decode().split()
        logger.debug("Found %d unread messages", len(message_numbers))

        for num in message_numbers:
            # Ensure message number is properly formatted for IMAP
            _, msg_data = await self._imap.fetch(str(num).encode(), "(RFC822)")
            if not msg_data or not msg_data[0]:
                logger.warning("No data returned for message %s", num)
                continue

            # IMAP fetch response format:
            # [(b'1 (RFC822 {size}', b'raw email data'), b')']
            # We need to ensure we're getting the actual email data
            email_data = msg_data[0]
            if isinstance(email_data, (list, tuple)) and len(email_data) > 1:
                email_body = email_data[1]
            else:
                logger.warning(
                    "Unexpected message data format for message %s: %s", num, email_data
                )
                continue

            if not isinstance(email_body, bytes):
                logger.warning(
                    "Email body is not bytes for message %s: %s", num, type(email_body)
                )
                continue

            # Create EmailMessage instead of Message
            email_message = email.message_from_bytes(
                email_body, policy=email.policy.default
            )
            if not isinstance(email_message, EmailMessage):
                email_message = EmailMessage()
                email_message.set_content(email_body.decode())

            # Convert to our EmailData format
            email_data = EmailData.from_email_message(email_message)
            yield email_data

    async def send_message(self, message: EmailData) -> None:
        """Send an email message via SMTP."""
        if not self._smtp:
            raise RuntimeError("Not connected to SMTP server")

        logger.debug("Sending message to %s", ", ".join(message.to_addresses))
        email_message = message.to_email_message()
        await self._smtp.send_message(email_message)
        logger.debug("Message sent successfully")

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read using its Message-ID."""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")

        # Search for the message by Message-ID
        _, data = await self._imap.search(f'HEADER "Message-ID" "{message_id}"')
        message_numbers = data[0].decode().split()

        if message_numbers:
            logger.debug("Marking message %s as read", message_id)
            # Mark the message as seen - ensure message number is properly formatted
            await self._imap.store(str(message_numbers[0]).encode(), "+FLAGS", "\\Seen")

    async def __aenter__(self) -> "EmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
