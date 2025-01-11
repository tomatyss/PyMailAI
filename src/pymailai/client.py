"""Email client implementation."""

import asyncio
import email
import logging
from email.message import EmailMessage
from typing import AsyncGenerator, Optional, cast

import aioimaplib
import aiosmtplib

from pymailai.base_client import BaseEmailClient
from pymailai.config import EmailConfig
from pymailai.message import EmailData

logger = logging.getLogger(__name__)


class EmailClient(BaseEmailClient):
    """Asynchronous email client for IMAP and SMTP operations."""

    def __init__(self, config: EmailConfig):
        """Initialize email client with configuration."""
        self.config = config
        self._imap: Optional[aioimaplib.IMAP4_SSL] = None
        self._smtp: Optional[aiosmtplib.SMTP] = None

    async def _connect_smtp(self) -> None:
        """Establish connection to SMTP server."""
        if self._smtp:
            try:
                await self._smtp.quit()
            except Exception:
                pass
            self._smtp = None

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

            # Use STARTTLS for port 587
            if self.config.smtp_port == 587:
                await self._smtp.starttls()
        await self._smtp.login(self.config.email, self.config.password)
        logger.debug("Logged in to SMTP server as %s", self.config.email)

    async def _ensure_smtp_connection(self) -> None:
        """Ensure SMTP connection is active and reconnect if needed."""
        try:
            if not self._smtp:
                await self._connect_smtp()
            else:
                # Test connection with NOOP
                try:
                    await self._smtp.noop()
                except Exception as e:
                    logger.warning("SMTP connection lost, reconnecting: %s", e)
                    await self._connect_smtp()
        except Exception as e:
            logger.error("Failed to ensure SMTP connection: %s", e)
            raise

    async def _connect_imap(self) -> None:
        """Establish connection to IMAP server."""
        if self._imap:
            try:
                await self._imap.logout()
            except Exception:
                pass
            self._imap = None

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

    async def _ensure_imap_connection(self) -> None:
        """Ensure IMAP connection is active and reconnect if needed."""
        try:
            if not self._imap:
                await self._connect_imap()
            else:
                # Test connection with NOOP
                try:
                    imap = cast(aioimaplib.IMAP4_SSL, self._imap)
                    await asyncio.wait_for(imap.noop(), timeout=self.config.timeout)
                except Exception as e:
                    logger.warning("IMAP connection lost, reconnecting: %s", e)
                    await self._connect_imap()
        except Exception as e:
            logger.error("Failed to ensure IMAP connection: %s", e)
            raise

    async def connect(self) -> None:
        """Establish connections to IMAP and SMTP servers."""
        await self._connect_imap()
        await self._connect_smtp()

    async def disconnect(self) -> None:
        """Close connections to email servers."""
        if self._imap:
            try:
                await self._imap.logout()
                logger.debug("Disconnected from IMAP server")
            except Exception as e:
                logger.warning("Error disconnecting from IMAP: %s", e)
            self._imap = None

        if self._smtp:
            try:
                await self._smtp.quit()
                logger.debug("Disconnected from SMTP server")
            except Exception as e:
                logger.warning("Error disconnecting from SMTP: %s", e)
            self._smtp = None

    async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
        """Fetch new unread messages from the IMAP server."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                await self._ensure_imap_connection()
                imap = cast(aioimaplib.IMAP4_SSL, self._imap)

                # Search for unread messages with timeout
                _, data = await asyncio.wait_for(
                    imap.search("UNSEEN"), timeout=self.config.timeout
                )
                break
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(
                        f"Failed to fetch messages after {max_retries} attempts: {e}"
                    )
                    raise
                wait_time = min(2**retry_count, 30)
                logger.warning(
                    f"Error fetching messages (attempt {retry_count}/{max_retries}), "
                    f"retrying in {wait_time} seconds: {e}"
                )
                await asyncio.sleep(wait_time)
        message_numbers = data[0].decode().split()
        logger.debug("Found %d unread messages", len(message_numbers))

        for num in message_numbers:
            fetch_retries = 0
            while fetch_retries < max_retries:
                try:
                    await self._ensure_imap_connection()
                    imap = cast(aioimaplib.IMAP4_SSL, self._imap)
                    # Format message number for IMAP - ensure it's a valid message set
                    _, msg_data = await asyncio.wait_for(
                        imap.fetch(num, "(RFC822)"), timeout=self.config.timeout
                    )
                    if not msg_data or not msg_data[0]:
                        logger.warning("No data returned for message %s", num)
                        break
                    break
                except Exception as e:
                    fetch_retries += 1
                    if fetch_retries == max_retries:
                        logger.error(
                            f"Failed to fetch message {num} after {max_retries} attempts: {e}"
                        )
                        break
                    wait_time = min(2**fetch_retries, 30)
                    logger.warning(
                        f"Error fetching message {num} (attempt {fetch_retries}/{max_retries}), "
                        f"retrying in {wait_time} seconds: {e}"
                    )
                    await asyncio.sleep(wait_time)

            if fetch_retries == max_retries:
                continue

            # When using RFC822, the email data is always the second element in the response
            email_body = msg_data[1]

            if not email_body:
                logger.warning(
                    "Could not find email body in message data for message %s", num
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

    async def send_message(self, message: EmailData, max_retries: int = 3) -> None:
        """Send an email message via SMTP with automatic reconnection and retries.

        Args:
            message: The email message to send
            max_retries: Maximum number of retry attempts (default: 3)
        """
        retries = 0
        last_error = None

        while retries <= max_retries:
            try:
                await self._ensure_smtp_connection()
                logger.debug("Sending message to %s", ", ".join(message.to_addresses))
                email_message = message.to_email_message()
                if self._smtp:
                    await self._smtp.send_message(email_message)
                logger.debug("Message sent successfully")
                return
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= max_retries:
                    wait_time = min(
                        2**retries, 30
                    )  # Exponential backoff, max 30 seconds
                    logger.warning(
                        "Failed to send message (attempt %d/%d), retrying in %d seconds: %s",
                        retries,
                        max_retries,
                        wait_time,
                        e,
                    )
                    await asyncio.sleep(wait_time)

        logger.error("Failed to send message after %d attempts", max_retries)
        raise last_error or RuntimeError("Failed to send message")

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read using its Message-ID."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                await self._ensure_imap_connection()
                imap = cast(aioimaplib.IMAP4_SSL, self._imap)

                # Search for the message by Message-ID with timeout
                _, data = await asyncio.wait_for(
                    imap.search(f'HEADER "Message-ID" "{message_id}"'),
                    timeout=self.config.timeout,
                )
                message_numbers = data[0].decode().split()

                if message_numbers:
                    logger.debug("Marking message %s as read", message_id)
                    # Mark the message as seen using the raw message number with timeout
                    await asyncio.wait_for(
                        imap.store(message_numbers[0], "+FLAGS", "\\Seen"),
                        timeout=self.config.timeout,
                    )
                return
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(2**retry_count, 30)
                    logger.warning(
                        f"Error marking message as read (attempt {retry_count}/{max_retries}), "
                        f"retrying in {wait_time} seconds: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to mark message as read after {max_retries} attempts: {e}"
                    )

    async def __aenter__(self) -> "EmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def query_messages(
        self, query_params: dict
    ) -> AsyncGenerator[EmailData, None]:
        """Query messages using IMAP search criteria.

        Args:
            query_params: Dictionary containing query parameters:
                - after_date: Optional[str] - Messages after this date (YYYY-MM-DD)
                - before_date: Optional[str] - Messages before this date (YYYY-MM-DD)
                - subject: Optional[str] - Subject line contains this text
                - from_address: Optional[str] - Sender email address
                - to_address: Optional[str] - Recipient email address
                - label: Optional[str] - Message folder (defaults to INBOX)
                - unread_only: Optional[bool] - Only unread messages if True
                - include_body: Optional[bool] - Include message body in results
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                await self._ensure_imap_connection()
                imap = cast(aioimaplib.IMAP4_SSL, self._imap)

                # Build IMAP search criteria
                search_criteria = []

                if query_params.get("after_date"):
                    search_criteria.append(f'SINCE "{query_params["after_date"]}"')
                if query_params.get("before_date"):
                    search_criteria.append(f'BEFORE "{query_params["before_date"]}"')
                if query_params.get("subject"):
                    search_criteria.append(f'SUBJECT "{query_params["subject"]}"')
                if query_params.get("from_address"):
                    search_criteria.append(f'FROM "{query_params["from_address"]}"')
                if query_params.get("to_address"):
                    search_criteria.append(f'TO "{query_params["to_address"]}"')
                if query_params.get("unread_only"):
                    search_criteria.append("UNSEEN")

                # If no criteria specified, search all messages
                search_command = " ".join(search_criteria) if search_criteria else "ALL"
                logger.debug(f"Executing IMAP search: {search_command}")

                # Switch to requested folder/label if specified
                if query_params.get("label"):
                    await imap.select(query_params["label"])

                # Execute search with timeout
                _, data = await asyncio.wait_for(
                    imap.search(search_command), timeout=self.config.timeout
                )
                break
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logger.error(
                        f"Failed to search messages after {max_retries} attempts: {e}"
                    )
                    raise
                wait_time = min(2**retry_count, 30)
                logger.warning(
                    f"Error searching messages (attempt {retry_count}/{max_retries}), "
                    f"retrying in {wait_time} seconds: {e}"
                )
                await asyncio.sleep(wait_time)

        message_numbers = data[0].decode().split()
        logger.debug(f"Found {len(message_numbers)} matching messages")

        for num in message_numbers:
            fetch_retries = 0
            while fetch_retries < max_retries:
                try:
                    await self._ensure_imap_connection()
                    imap = cast(aioimaplib.IMAP4_SSL, self._imap)

                    # Fetch message data
                    _, msg_data = await asyncio.wait_for(
                        imap.fetch(
                            num,
                            "(RFC822)"
                            if query_params.get("include_body")
                            else "(RFC822.HEADER)",
                        ),
                        timeout=self.config.timeout,
                    )
                    if not msg_data or not msg_data[0]:
                        logger.warning(f"No data returned for message {num}")
                        break
                    break
                except Exception as e:
                    fetch_retries += 1
                    if fetch_retries == max_retries:
                        logger.error(
                            f"Failed to fetch message {num} after {max_retries} attempts: {e}"
                        )
                        break
                    wait_time = min(2**fetch_retries, 30)
                    logger.warning(
                        f"Error fetching message {num} (attempt {fetch_retries}/{max_retries}), "
                        f"retrying in {wait_time} seconds: {e}"
                    )
                    await asyncio.sleep(wait_time)

            if fetch_retries == max_retries:
                continue

            # When using RFC822, the email data is always the second element in the response
            email_body = msg_data[1]

            if not email_body:
                logger.warning(
                    f"Could not find email body in message data for message {num}"
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
