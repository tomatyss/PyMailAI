"""Configuration handling for PyMailAI."""

from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Email configuration settings."""

    imap_server: str
    smtp_server: str
    email: str
    password: str
    imap_port: int = 993
    smtp_port: int = 587
    folder: str = "INBOX"
    check_interval: int = 60  # seconds
    max_retries: int = 3
    timeout: int = 30  # seconds
    tls: bool = True

    def validate(self) -> None:
        """Validate configuration settings."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validate_email(self.email)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {e}")

        if not self.password:
            raise ValueError("Password cannot be empty")

        if not self.imap_server or not self.smtp_server:
            raise ValueError("IMAP and SMTP servers must be specified")
