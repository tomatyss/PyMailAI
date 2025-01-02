"""Email reply building utilities."""

from datetime import datetime
from typing import Optional


class ReplyBuilder:
    """Handles building email replies."""

    @staticmethod
    def build_reply_body(
        original_text: str,
        reply_text: str,
        quote_level: int = 1,
        include_history: bool = True,
        subject: str = "",
        timestamp: Optional[datetime] = None,
        from_address: str = "",
    ) -> str:
        """Build reply body with proper formatting."""
        if not include_history:
            return reply_text

        prefix = ">" * quote_level
        quoted_header = [
            "",
            "",
            f"{prefix} -------- Original Message --------",
            f"{prefix} Subject: {subject}",
            f"{prefix} Date: "
            f"{timestamp.strftime('%b %d, %Y, at %I:%M %p') if timestamp else 'N/A'}",
            f"{prefix} From: {from_address}",
            prefix,
        ]

        quoted_body = []
        for line in original_text.splitlines():
            if line.startswith(">"):
                quoted_body.append(f"{prefix} {line}")
            else:
                quoted_body.append(f"{prefix} {line}" if line.strip() else prefix)

        return reply_text + "\n".join(quoted_header + quoted_body)
