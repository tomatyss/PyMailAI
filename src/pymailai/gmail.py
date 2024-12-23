"""Gmail credential handling for PyMailAI."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from google.oauth2.credentials import Credentials

from .config import EmailConfig


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid or missing required fields."""

    pass


@dataclass
class GmailCredentials:
    """Gmail OAuth2 credentials."""

    client_id: str
    client_secret: str
    refresh_token: str
    token_uri: str = "https://oauth2.googleapis.com/token"
    scopes: Optional[List[str]] = None
    email: Optional[str] = None

    def __post_init__(self):
        """Validate credentials after initialization."""
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise InvalidCredentialsError("Missing required credential fields")

        if self.scopes is None:
            self.scopes = ["https://www.googleapis.com/auth/gmail.modify"]

    def to_oauth_credentials(self) -> Credentials:
        """Convert to Google OAuth2 credentials."""
        try:
            # Create OAuth credentials
            from google.oauth2.credentials import Credentials

            return Credentials(
                None,  # token - will be refreshed
                refresh_token=self.refresh_token,
                token_uri=self.token_uri,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes,
            )
        except (ValueError, TypeError) as e:
            # Handle validation errors
            raise InvalidCredentialsError(f"Invalid OAuth credentials: {e}")

    def to_email_config(self) -> EmailConfig:
        """Convert to EmailConfig for use with EmailClient."""
        return EmailConfig(
            email=self.email or "",
            password=self.refresh_token,  # Use refresh token as password
            imap_server="imap.gmail.com",
            smtp_server="smtp.gmail.com",
            imap_port=993,
            smtp_port=587,
            tls=True,
        )

    def __str__(self) -> str:
        """Show credentials without sensitive data."""
        return (
            f"GmailCredentials(client_id='{self.client_id}', "
            f"token_uri='{self.token_uri}', "
            f"scopes={self.scopes})"
        )


def load_credentials(path: Union[str, Path]) -> GmailCredentials:
    """Load Gmail credentials from a JSON file.

    Args:
        path: Path to credentials JSON file

    Returns:
        GmailCredentials instance

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        InvalidCredentialsError: If credentials are invalid or missing fields
    """
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError:
        raise InvalidCredentialsError("Invalid JSON in credentials file")

    try:
        return GmailCredentials(**data)
    except (TypeError, ValueError) as e:
        raise InvalidCredentialsError(f"Invalid credentials format: {e}")


def create_from_oauth_credentials(
    creds: dict,
    save_path: Optional[Union[str, Path]] = None,
) -> GmailCredentials:
    """Create Gmail credentials from OAuth2 credentials.

    Args:
        creds: Dictionary containing OAuth2 credentials
        save_path: Optional path to save credentials JSON file

    Returns:
        GmailCredentials instance

    Raises:
        InvalidCredentialsError: If credentials are invalid
    """
    # Validate required fields first
    if not all(
        creds.get(field) for field in ["client_id", "client_secret", "refresh_token"]
    ):
        raise InvalidCredentialsError("Missing required fields")

    try:
        # Create Gmail credentials
        gmail_creds = GmailCredentials(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            refresh_token=creds["refresh_token"],
            token_uri=creds.get("token_uri", "https://oauth2.googleapis.com/token"),
            scopes=creds.get("scopes"),
            email=creds.get("email"),
        )

        # Try creating OAuth credentials to validate
        try:
            gmail_creds.to_oauth_credentials()
        except InvalidCredentialsError as e:
            raise InvalidCredentialsError(f"Invalid OAuth credentials: {e}")

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(
                    {
                        "client_id": gmail_creds.client_id,
                        "client_secret": gmail_creds.client_secret,
                        "refresh_token": gmail_creds.refresh_token,
                        "token_uri": gmail_creds.token_uri,
                        "scopes": gmail_creds.scopes,
                        "email": gmail_creds.email,
                    },
                    f,
                    indent=2,
                )

        return gmail_creds
    except KeyError as e:
        raise InvalidCredentialsError(f"Missing required field: {e}")
    except InvalidCredentialsError:
        raise
    except Exception as e:
        raise InvalidCredentialsError(f"Failed to create credentials: {e}")
