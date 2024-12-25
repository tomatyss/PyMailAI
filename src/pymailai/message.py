"""Email message data structures and utilities."""

from dataclasses import dataclass
from datetime import datetime
from email import utils
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EmailData:
    """Represents processed email data."""

    message_id: str
    subject: str
    from_address: str
    to_addresses: List[str]
    cc_addresses: List[str]
    body_text: str
    body_html: Optional[str]
    timestamp: datetime
    references: Optional[List[str]] = None
    in_reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = None  # type: ignore

    def __post_init__(self) -> None:
        """Initialize empty lists for None values."""
        self.attachments = [] if self.attachments is None else self.attachments
        self.references = [] if self.references is None else self.references

    @classmethod
    def from_email_message(cls, msg: EmailMessage) -> "EmailData":
        """Create EmailData from an email.message.EmailMessage object."""
        body_text = ""
        body_html = None
        attachments = []

        # Process message parts
        if msg.is_multipart():
            for part in msg.walk():
                if part.is_multipart():
                    continue

                content_type = part.get_content_type()
                disposition = part.get("Content-Disposition", "")

                if "attachment" in disposition:
                    attachments.append(
                        {
                            "filename": part.get_filename(),
                            "content_type": content_type,
                            "payload": part.get_payload(decode=True),
                        }
                    )
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    assert isinstance(payload, bytes)  # type assertion for mypy
                    body_text = payload.decode()
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    assert isinstance(payload, bytes)  # type assertion for mypy
                    body_html = payload.decode()
        else:
            payload = msg.get_payload(decode=True)
            assert isinstance(payload, bytes)  # type assertion for mypy
            body_text = payload.decode()

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

    @staticmethod
    def _format_quoted_text(text: str, level: int = 1) -> str:
        """Format text with email-style quotation marks.

        Args:
            text: The text to quote
            level: The quotation level (number of '>' characters to prepend)

        Returns:
            The quoted text with '>' characters prepended to each line
        """
        prefix = ">" * level
        return "\n".join(
            f"{prefix} {line}" if line.strip() else prefix for line in text.splitlines()
        )

    def create_reply(
        self, reply_text: str, include_history: bool = True, quote_level: int = 1
    ) -> "EmailData":
        """Create a reply EmailData object with proper threading fields set.

        Args:
            reply_text: The text of the reply message
            include_history: Whether to include quoted message history
            quote_level: The quotation level for the previous message

        Returns:
            A new EmailData object configured as a reply to this message
        """
        # Build references list
        new_references = [] if self.references is None else self.references.copy()
        if self.message_id:
            new_references.append(self.message_id)

        # Format body text with quotations if including history
        body_text = reply_text
        if include_history:
            quoted = self._format_quoted_text(self.body_text, quote_level)
            body_text = f"{reply_text}\n\n{quoted}"

        # Create reply email data
        return EmailData(
            message_id="",  # Will be set by email server
            subject=f"Re: {self.subject}"
            if not self.subject.startswith("Re: ")
            else self.subject,
            from_address="",  # Should be set by caller
            to_addresses=[self.from_address],
            cc_addresses=self.cc_addresses,
            body_text=body_text,
            body_html=None,  # HTML version would need to be generated separately
            timestamp=datetime.now(),
            references=new_references,
            in_reply_to=self.message_id,
            attachments=[],
        )

    def to_email_message(self) -> EmailMessage:
        """Convert EmailData to an email.message.EmailMessage object."""
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

        # Start with mixed if we have attachments
        if self.attachments:
            msg.make_mixed()

            # Create content part
            content = EmailMessage()
            if self.body_html:
                content.make_alternative()
                content.add_alternative(self.body_text, subtype="plain")
                content.add_alternative(self.body_html, subtype="html")
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
            if self.body_html:
                msg.make_alternative()
                msg.add_alternative(self.body_text, subtype="plain")
                msg.add_alternative(self.body_html, subtype="html")
            else:
                msg.set_content(self.body_text)

        return msg
