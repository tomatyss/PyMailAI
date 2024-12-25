"""Gmail API client implementation."""

import base64
import logging
from datetime import datetime
from email import utils
from typing import AsyncGenerator

from pymailai.base_client import BaseEmailClient
from pymailai.message import EmailData

logger = logging.getLogger(__name__)


class GmailClient(BaseEmailClient):
    """Asynchronous Gmail client using the Gmail API."""

    def __init__(self, service):
        """Initialize Gmail client with service."""
        self.service = service

    async def connect(self) -> None:
        """No connection needed for Gmail API."""
        logger.info("Gmail API client ready")

    async def disconnect(self) -> None:
        """No disconnection needed for Gmail API."""
        logger.info("Gmail API client closed")

    async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
        """Fetch new unread messages using Gmail API."""
        try:
            # Search for unread messages
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q="is:unread -in:chats")
                .execute()
            )

            messages = results.get("messages")
            if not messages:
                logger.info("No unread messages found")
                return

            logger.info(f"Found {len(messages)} unread messages")

            for message in messages:
                try:
                    # Get full message details
                    msg = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=message["id"], format="full")
                        .execute()
                    )

                    # Create EmailData directly with Gmail message ID
                    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

                    # Extract body
                    body_text = None
                    body_html = None

                    def extract_parts(part):
                        nonlocal body_text, body_html

                        if part.get("mimeType") == "multipart/alternative":
                            # Handle nested multipart/alternative
                            for subpart in part.get("parts", []):
                                extract_parts(subpart)
                        elif part.get("mimeType") == "multipart/mixed":
                            # Handle nested multipart/mixed
                            for subpart in part.get("parts", []):
                                extract_parts(subpart)
                        elif part.get("mimeType") == "text/plain":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                body_text = base64.urlsafe_b64decode(data).decode()
                        elif part.get("mimeType") == "text/html":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                body_html = base64.urlsafe_b64decode(data).decode()

                    # Start extraction from the payload
                    if msg["payload"].get("mimeType", "").startswith("multipart/"):
                        extract_parts(msg["payload"])
                    else:
                        # Single part message
                        data = msg["payload"]["body"].get("data", "")
                        if data:
                            content = base64.urlsafe_b64decode(data).decode()
                            if msg["payload"]["mimeType"] == "text/html":
                                body_html = content
                            else:
                                body_text = content

                    # Parse timestamp from headers or use message internal date
                    date_str = headers.get("Date")
                    if date_str:
                        timestamp = utils.parsedate_to_datetime(date_str)
                    else:
                        # Use internal date (Unix timestamp in seconds)
                        timestamp = datetime.fromtimestamp(
                            int(msg["internalDate"]) / 1000
                        )

                    # Create EmailData with Gmail message ID
                    email_data = EmailData(
                        message_id=msg["id"],  # Use Gmail message ID directly
                        subject=headers.get("Subject", ""),
                        from_address=headers.get("From", ""),
                        to_addresses=[
                            addr.strip()
                            for addr in headers.get("To", "").split(",")
                            if addr.strip()
                        ],
                        cc_addresses=[
                            addr.strip()
                            for addr in headers.get("Cc", "").split(",")
                            if addr.strip()
                        ],
                        body_text=body_text or "",
                        body_html=body_html,
                        timestamp=timestamp,
                        references=headers.get("References", ""),
                        in_reply_to=headers.get("In-Reply-To", ""),
                    )
                    yield email_data

                except Exception as e:
                    logger.error(f"Failed to process message {message['id']}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Failed to fetch messages: {str(e)}")

    async def send_message(self, message: EmailData) -> None:
        """Send an email message via Gmail API."""
        try:
            # Convert to EmailMessage
            email_message = message.to_email_message()

            # Encode the message
            encoded_message = base64.urlsafe_b64encode(
                email_message.as_bytes()
            ).decode()

            # Create the Gmail API message
            gmail_message = {"raw": encoded_message}

            # Send the message
            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=gmail_message)
                .execute()
            )

            logger.info(f"Message sent successfully with ID: {result.get('id')}")

        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise

    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read using Gmail API.

        Args:
            message_id: Gmail message ID to mark as read
        """
        try:
            # Directly modify the message using its Gmail ID
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            logger.info(f"Marked message {message_id} as read")
        except Exception as e:
            logger.error(f"Failed to mark message as read: {str(e)}")

    async def __aenter__(self) -> "GmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
