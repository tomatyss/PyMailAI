"""Email client implementation."""

import asyncio
import email
from email.message import EmailMessage
from typing import AsyncGenerator, Optional, List

import aioimaplib
import aiosmtplib

from pymailai.config import EmailConfig
from pymailai.message import EmailData


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
            timeout=self.config.timeout
        )
        await self._imap.wait_hello_from_server()
        await self._imap.login(self.config.email, self.config.password)
        await self._imap.select(self.config.folder)

        # Connect to SMTP
        self._smtp = aiosmtplib.SMTP(
            hostname=self.config.smtp_server,
            port=self.config.smtp_port,
            timeout=self.config.timeout,
            use_tls=self.config.tls
        )
        await self._smtp.connect()
        await self._smtp.login(self.config.email, self.config.password)

    async def disconnect(self) -> None:
        """Close connections to email servers."""
        if self._imap:
            await self._imap.logout()
            self._imap = None
        if self._smtp:
            await self._smtp.quit()
            self._smtp = None

    async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
        """Fetch new unread messages from the IMAP server."""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")

        # Search for unread messages
        _, data = await self._imap.search("UNSEEN")
        message_numbers = data[0].split()

        for num in message_numbers:
            _, msg_data = await self._imap.fetch(num, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body, policy=email.policy.default)
            
            # Convert to our EmailData format
            email_data = EmailData.from_email_message(email_message)
            yield email_data

    async def send_message(self, message: EmailData) -> None:
        """Send an email message via SMTP."""
        if not self._smtp:
            raise RuntimeError("Not connected to SMTP server")

        email_message = message.to_email_message()
        await self._smtp.send_message(email_message)

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read using its Message-ID."""
        if not self._imap:
            raise RuntimeError("Not connected to IMAP server")

        # Search for the message by Message-ID
        _, data = await self._imap.search(f'HEADER "Message-ID" "{message_id}"')
        message_numbers = data[0].split()

        if message_numbers:
            # Mark the message as seen
            await self._imap.store(message_numbers[0], "+FLAGS", "\\Seen")

    async def __aenter__(self) -> "EmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
