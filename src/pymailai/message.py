"""Email message data structures and utilities."""

from dataclasses import dataclass
from datetime import datetime
from email import utils
from email.message import EmailMessage
from typing import Any, Dict, List, Optional


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

    @classmethod
    def from_email_message(cls, msg: EmailMessage) -> "EmailData":
        """Create EmailData from an email.message.EmailMessage object."""
        body_text = ""
        body_html = None
        attachments = []

        # Process message parts
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode()
                elif part.get_filename():  # Has attachment
                    attachments.append(
                        {
                            "filename": part.get_filename(),
                            "content_type": content_type,
                            "payload": part.get_payload(decode=True),
                        }
                    )
        else:
            body_text = msg.get_payload(decode=True).decode()

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
                utils.mktime_tz(
                    utils.parsedate_tz(msg["Date"]) or (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                )
            ),
            references=[ref.strip() for ref in (msg["References"] or "").split()],
            in_reply_to=msg["In-Reply-To"],
            attachments=attachments,
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

        # Handle message content
        if self.body_html:
            # Create multipart/alternative for HTML and text
            msg.make_alternative()
            msg.add_alternative(self.body_text, subtype="plain")
            msg.add_alternative(self.body_html, subtype="html")

            # If there are attachments, convert to multipart/mixed
            if self.attachments:
                msg_alt = msg
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

                msg.make_mixed()
                msg.attach(msg_alt)

                # Add attachments
                for attachment in self.attachments:
                    msg.add_attachment(
                        attachment["payload"],
                        maintype=attachment["content_type"].split("/")[0],
                        subtype=attachment["content_type"].split("/")[1],
                        filename=attachment["filename"],
                    )
        else:
            # Text-only message
            if self.attachments:
                msg.make_mixed()
                msg.add_alternative(self.body_text, subtype="plain")

                # Add attachments
                for attachment in self.attachments:
                    msg.add_attachment(
                        attachment["payload"],
                        maintype=attachment["content_type"].split("/")[0],
                        subtype=attachment["content_type"].split("/")[1],
                        filename=attachment["filename"],
                    )
            else:
                # Simple text-only message without attachments
                msg.set_content(self.body_text)

        return msg
