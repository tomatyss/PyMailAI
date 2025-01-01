"""Email message data structures and utilities."""

from dataclasses import dataclass, field
from datetime import datetime
from email import utils
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

from pymailai.email_processor import EmailProcessor
from pymailai.email_reply import ReplyBuilder
from pymailai.email_validator import EmailValidator
from pymailai.markdown_converter import MarkdownConverter


@dataclass
class EmailData:
    """Represents processed email data."""

    message_id: str
    subject: str
    from_address: str
    to_addresses: List[str]
    cc_addresses: List[str] = field(default_factory=list)
    body_text: str = ""
    body_html: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    references: List[str] = field(default_factory=list)
    in_reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize and validate email data."""
        # Ensure references is a list of strings
        if not isinstance(self.references, list):
            raise ValueError("References must be a list of strings")

        # Clean up reference strings
        self.references = [ref.strip() for ref in self.references if ref]

        # Validate non-empty addresses
        if self.from_address and not EmailValidator.validate_email(self.from_address):
            raise ValueError(f"Invalid from address: {self.from_address}")

        if self.to_addresses and not EmailValidator.validate_addresses(
            self.to_addresses
        ):
            raise ValueError("Invalid to addresses")

        if self.cc_addresses and not EmailValidator.validate_addresses(
            self.cc_addresses
        ):
            raise ValueError("Invalid cc addresses")

    @classmethod
    def from_email_message(cls, msg: EmailMessage) -> "EmailData":
        """Create EmailData from an EmailMessage object."""
        body_text, body_html, attachments = EmailProcessor.process_message_parts(msg)

        return cls(
            message_id=msg["Message-ID"] or "",
            subject=msg["Subject"] or "",
            from_address=msg["From"] or "",
            to_addresses=[
                addr.strip() for addr in (msg["To"] or "").split(",") if addr
            ],
            cc_addresses=[
                addr.strip() for addr in (msg["Cc"] or "").split(",") if addr
            ],
            body_text=body_text,
            body_html=body_html,
            timestamp=datetime.fromtimestamp(
                utils.mktime_tz(cls._get_valid_date_tuple(msg["Date"]))
            ),
            references=[ref.strip() for ref in (msg["References"] or "").split()],
            in_reply_to=msg["In-Reply-To"],
            attachments=attachments,
        )

    @staticmethod
    def _get_valid_date_tuple(
        date_str: Optional[str],
    ) -> Tuple[int, int, int, int, int, int, int, int, int, Optional[int]]:
        """Get a valid date tuple from a date string, using current time as fallback."""
        default_tuple = utils.parsedate_tz(utils.formatdate(localtime=True))
        assert (
            default_tuple is not None
        )  # formatdate() always returns a valid date string

        if date_str is None:
            return default_tuple

        parsed = utils.parsedate_tz(date_str)
        return parsed if parsed is not None else default_tuple

    def create_reply(
        self, reply_text: str, include_history: bool = True, quote_level: int = 1
    ) -> "EmailData":
        """Create a reply EmailData object with proper threading fields set.

        Args:
            reply_text: The text of the reply message
            include_history: Whether to include quoted message history
            quote_level: The quotation level for the previous message
        """
        if not self.to_addresses:
            raise ValueError("Cannot create reply: original message has no recipients")

        # Build references list
        new_references = list(self.references)  # Convert to list and copy
        if self.message_id:
            new_references.append(self.message_id)

        # Build reply body with proper formatting
        body_text = ReplyBuilder.build_reply_body(
            original_text=self.body_text,
            reply_text=reply_text,
            quote_level=quote_level,
            include_history=include_history,
            subject=self.subject,
            timestamp=self.timestamp,
            from_address=self.from_address,
        )

        # Create reply email data
        return EmailData(
            message_id="",  # Will be set by email server
            subject=f"Re: {self.subject}"
            if not self.subject.startswith("Re: ")
            else self.subject,
            from_address=self.to_addresses[0],  # Use the first recipient as sender
            to_addresses=[self.from_address],
            cc_addresses=self.cc_addresses,
            body_text=body_text,
            body_html=None,  # HTML version would need to be generated separately
            timestamp=datetime.now(),
            references=new_references,
            in_reply_to=self.message_id,
        )

    def to_email_message(self) -> EmailMessage:
        """Convert EmailData to an EmailMessage object."""
        msg = EmailMessage()
        msg["Subject"] = self.subject
        msg["From"] = self.from_address
        msg["To"] = ", ".join(self.to_addresses)
        if self.cc_addresses:
            msg["Cc"] = ", ".join(self.cc_addresses)
        if self.in_reply_to:
            msg["In-Reply-To"] = self.in_reply_to
        if self.references:
            msg["References"] = " ".join(self.references)

        # Convert markdown to HTML if needed
        html_content = self._get_html_content()

        # Set message content
        self._set_message_content(msg, html_content)

        return msg

    def _get_html_content(self) -> Optional[str]:
        """Get HTML content, converting from markdown if needed."""
        if self.body_html:
            return self.body_html

        # Convert markdown to HTML if text appears to be markdown
        if any(
            marker in self.body_text for marker in ["```", "#", "**", "__", ">", "-"]
        ):
            converter = MarkdownConverter()
            return converter.convert(self.body_text)

        return None

    def _set_message_content(
        self, msg: EmailMessage, html_content: Optional[str]
    ) -> None:
        """Set the message content including attachments."""
        if self.attachments:
            msg.make_mixed()
            content = EmailMessage()

            if html_content:
                content.make_alternative()
                content.add_alternative(self.body_text, subtype="plain")
                content.add_alternative(html_content, subtype="html")
            else:
                content.set_content(self.body_text)

            msg.attach(content)

            # Add attachments
            for attachment in self.attachments:
                msg.add_attachment(
                    attachment["payload"],
                    maintype=attachment["content_type"].split("/")[0],
                    subtype=attachment["content_type"].split("/")[1],
                    filename=attachment["filename"],
                )
        else:
            # No attachments
            if html_content:
                msg.make_alternative()
                msg.add_alternative(self.body_text, subtype="plain")
                msg.add_alternative(html_content, subtype="html")
            else:
                msg.set_content(self.body_text)
