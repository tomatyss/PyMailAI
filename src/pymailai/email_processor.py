"""Email message processing utilities."""

from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

from pymailai.html_converter import HtmlConverter
from pymailai.text_processor import TextProcessor


class EmailProcessor:
    """Handles processing of email message parts."""

    @staticmethod
    def process_message_parts(
        msg: EmailMessage,
    ) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """Process message parts and return body text, html and attachments."""
        body_text_parts = []
        body_html = None
        attachments = []

        # Process all parts of the message
        if msg.is_multipart():
            # First pass: collect all parts
            text_parts = []
            html_parts = []

            for part in msg.walk():
                if part.is_multipart():
                    continue

                content_type = part.get_content_type()
                disposition = part.get("Content-Disposition", "")

                if "attachment" in disposition or content_type.startswith("image/"):
                    attachments.append(
                        {
                            "filename": part.get_filename(),
                            "content_type": content_type,
                            "payload": part.get_payload(decode=True),
                        }
                    )
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    assert isinstance(payload, bytes)
                    text_parts.append(payload.decode())
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    assert isinstance(payload, bytes)
                    html_parts.append(payload.decode())

            # Second pass: process collected parts
            if text_parts:
                body_text_parts.extend(text_parts)
            elif html_parts:
                # If we only have HTML parts, convert to text while preserving quotes
                body_text_parts.append(
                    HtmlConverter.convert_html_to_text(html_parts[0])
                )

            if html_parts:
                body_html = html_parts[0]  # Use the first HTML part

        else:
            # Single part message
            payload = msg.get_payload(decode=True)
            assert isinstance(payload, bytes)
            content = payload.decode()

            if msg.get_content_type() == "text/html":
                body_html = content
                body_text_parts.append(HtmlConverter.convert_html_to_text(content))
            else:
                # Process plain text while preserving quotes
                body_text_parts.append(TextProcessor.process_text_with_quotes(content))

        body_text = TextProcessor.combine_text_parts(body_text_parts)
        return body_text, body_html, attachments
