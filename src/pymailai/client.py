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
            try:
                # Format message number for IMAP - ensure it's a valid message set
                _, msg_data = await self._imap.fetch(num, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    logger.warning("No data returned for message %s", num)
                    continue
            except Exception as e:
                logger.error(f"Failed to fetch message {num}: {str(e)}")
                continue

            # IMAP fetch response can vary between servers
            # Some return: [(b'1 (RFC822 {size}', b'raw email data'), b')']
            # Others return: [b'28 FETCH (FLAGS (\\Seen) RFC822 {5324}', b'raw email data', b')']
            logger.debug("Raw IMAP response for message %s: %s", num, msg_data)

            email_body = None
            for i, part in enumerate(msg_data):
                logger.debug("Processing part %d: %s", i, part)
                if isinstance(part, (list, tuple)):
                    # Handle nested structure
                    for j, item in enumerate(part):
                        logger.debug("Processing nested item %d: %s", j, item)
                        if isinstance(item, bytes):
                            # Look for the actual email content
                            # It should be a large chunk of bytes that doesn't start with FETCH
                            # and isn't just a closing parenthesis
                            if len(item) > 100 or (
                                not item.startswith(b"FETCH")
                                and not item.endswith(b")")
                            ):
                                email_body = item
                                logger.debug("Found email body in nested structure")
                                break
                elif isinstance(part, bytes):
                    # Same logic for non-nested parts
                    if len(part) > 100 or (
                        not part.startswith(b"FETCH") and not part.endswith(b")")
                    ):
                        email_body = part
                        logger.debug("Found email body in flat structure")
                        break

            if not email_body:
                logger.warning(
                    "Could not find email body in message data for message %s: %s",
                    num,
                    msg_data,
                )
                continue

            # Parse email message
            try:
                email_message = email.message_from_bytes(
                    email_body, policy=email.policy.default
                )
                if not isinstance(email_message, EmailMessage):
                    # Convert Message to EmailMessage if needed
                    temp_message = EmailMessage()
                    temp_message.set_content(email_message.as_string())
                    email_message = temp_message
            except Exception as e:
                logger.error(f"Failed to parse email message: {str(e)}")
                continue

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
            try:
                logger.debug("Marking message %s as read", message_id)
                # Mark the message as seen using the raw message number
                await self._imap.store(message_numbers[0], "+FLAGS", "\\Seen")
            except Exception as e:
                logger.error(f"Failed to mark message {message_id} as read: {str(e)}")

    async def __aenter__(self) -> "EmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
