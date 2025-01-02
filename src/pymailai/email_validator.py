"""Email field validation utilities."""

import re
from typing import List


class EmailValidator:
    """Validates email fields."""

    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email address format."""
        return bool(cls.EMAIL_REGEX.match(email))

    @classmethod
    def validate_addresses(cls, addresses: List[str]) -> bool:
        """Validate list of email addresses."""
        return all(cls.validate_email(addr) for addr in addresses if addr)
