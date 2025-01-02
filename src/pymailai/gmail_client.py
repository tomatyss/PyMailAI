"""Gmail API client implementation."""

import base64
import logging
from datetime import datetime
from email import utils
from typing import AsyncGenerator, Optional, Tuple

from pymailai.base_client import BaseEmailClient
from pymailai.email_reply import ReplyBuilder
from pymailai.message import EmailData
from pymailai.text_processor import TextProcessor

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
                    # Get the thread ID first
                    msg = (
                        self.service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=message["id"],
                            format="metadata",
                            metadataHeaders=["threadId"],
                        )
                        .execute()
                    )

                    # Get all messages in the thread
                    thread = (
                        self.service.users()
                        .threads()
                        .get(userId="me", id=msg["threadId"])
                        .execute()
                    )

                    # Process all messages in the thread to build conversation history
                    thread_parts = []
                    thread_html_parts = []

                    # Process messages in chronological order (oldest first)
                    messages_in_thread = thread["messages"]
                    is_conversation = len(messages_in_thread) > 1

                    for thread_msg in messages_in_thread:
                        headers = {
                            h["name"]: h["value"]
                            for h in thread_msg["payload"]["headers"]
                        }
                        msg_text, msg_html = self._extract_message_content(
                            thread_msg["payload"]
                        )

                        if msg_text:
                            processed_text = TextProcessor.process_text_with_quotes(
                                msg_text
                            )
                            if is_conversation:
                                # Parse timestamp from headers
                                date_str = headers.get("Date")
                                if date_str:
                                    timestamp = utils.parsedate_to_datetime(date_str)
                                else:
                                    timestamp = datetime.fromtimestamp(
                                        int(thread_msg["internalDate"]) / 1000
                                    )

                                # Use ReplyBuilder to format the message
                                thread_parts.append(
                                    ReplyBuilder.build_reply_body(
                                        original_text=processed_text,
                                        reply_text="",
                                        subject=headers.get("Subject", ""),
                                        timestamp=timestamp,
                                        from_address=headers.get("From", ""),
                                    )
                                )
                            else:
                                thread_parts.append(processed_text)

                        if msg_html:
                            if is_conversation:
                                # Parse timestamp from headers
                                date_str = headers.get("Date")
                                if date_str:
                                    timestamp = utils.parsedate_to_datetime(date_str)
                                else:
                                    timestamp = datetime.fromtimestamp(
                                        int(thread_msg["internalDate"]) / 1000
                                    )

                                # Add HTML with quote formatting
                                thread_html_parts.append(
                                    f'<div class="email-quote">{msg_html}</div>'
                                )
                            else:
                                thread_html_parts.append(msg_html)
                        elif (
                            msg_text
                            and not msg_html
                            and thread_msg["payload"]
                            .get("mimeType", "")
                            .startswith("multipart/")
                        ):
                            # Only convert text to HTML for multipart messages
                            thread_html_parts.append(f"<pre>{msg_text}</pre>")

                    # Use the last message's headers for the email metadata
                    last_msg = thread["messages"][-1]
                    headers = {
                        h["name"]: h["value"] for h in last_msg["payload"]["headers"]
                    }

                    # Combine thread history
                    body_text = TextProcessor.combine_text_parts(
                        list(reversed(thread_parts))
                    )
                    body_html = (
                        "<br><br>".join(reversed(thread_html_parts))
                        if thread_html_parts
                        else None
                    )

                    # Parse timestamp from headers or use message internal date
                    date_str = headers.get("Date")
                    if date_str:
                        timestamp = utils.parsedate_to_datetime(date_str)
                    else:
                        # Use internal date (Unix timestamp in seconds)
                        timestamp = datetime.fromtimestamp(
                            int(msg["internalDate"]) / 1000
                        )

                    # Create EmailData with the original unread message ID
                    email_data = EmailData(
                        message_id=message["id"],  # Use the original unread message ID
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
                        references=[
                            ref.strip()
                            for ref in headers.get("References", "").split()
                            if ref.strip()
                        ],
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

    def _extract_message_content(
        self, payload: dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract text and HTML content from a Gmail message payload.

        Args:
            payload: Gmail message payload dictionary

        Returns:
            Tuple of (plain_text_content, html_content)
        """

        def decode_part(part: dict) -> Optional[str]:
            """Decode content from a message part."""
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode()
            return None

        def extract_content_recursive(
            part: dict,
        ) -> Tuple[Optional[str], Optional[str]]:
            """Recursively extract text and HTML content from message parts."""
            mime_type = part.get("mimeType", "")

            if mime_type.startswith("multipart/"):
                text = None
                html = None
                for subpart in part.get("parts", []):
                    subtext, subhtml = extract_content_recursive(subpart)
                    if subtext and not text:
                        text = subtext
                    if subhtml and not html:
                        html = subhtml
                return text, html
            else:
                content = decode_part(part)
                if content:
                    if mime_type == "text/plain":
                        return content, None
                    elif mime_type == "text/html":
                        return None, content
            return None, None

        return extract_content_recursive(payload)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
