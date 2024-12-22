"""Gmail credential handling for PyMailAI."""

import json
import os
from pathlib import Path
from typing import Optional, TypedDict, Union

from .config import EmailConfig


class GmailCredentialsDict(TypedDict):
    """Type definition for Gmail credentials dictionary."""

    client_id: str
    client_secret: str
    refresh_token: str
    token_uri: str
    type: str


class GmailCredentials:
    """Handler for Gmail credentials loaded from files."""

    def __init__(self, credentials_path: Union[str, Path]):
        """Initialize Gmail credentials handler.

        Args:
            credentials_path: Path to the credentials JSON file
        """
        self.credentials_path = Path(credentials_path)
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

        self._credentials: GmailCredentialsDict = self._load_credentials()

    def _load_credentials(self) -> GmailCredentialsDict:
        """Load credentials from JSON file."""
        try:
            with open(self.credentials_path) as f:
                creds: GmailCredentialsDict = json.load(f)
                return creds
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials file: {e}")

    @classmethod
    def from_oauth_credentials(
        cls,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        token_uri: str = "https://oauth2.googleapis.com/token",
        save_path: Optional[Union[str, Path]] = None,
    ) -> "GmailCredentials":
        """Create credentials from OAuth2 details.

        Args:
            client_id: Google OAuth2 client ID
            client_secret: Google OAuth2 client secret
            refresh_token: OAuth2 refresh token
            token_uri: OAuth2 token URI (default: Google's token endpoint)
            save_path: Optional path to save credentials JSON file

        Returns:
            GmailCredentials instance
        """
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "token_uri": token_uri,
            "type": "authorized_user",
        }

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(creds, f, indent=2)
            return cls(save_path)

        # If no save path, create temporary file
        tmp_path = Path(os.getenv("TMPDIR", "/tmp")) / "gmail_creds.json"
        with open(tmp_path, "w") as f:
            json.dump(creds, f, indent=2)
        return cls(tmp_path)

    def to_email_config(self, email_address: str) -> EmailConfig:
        """Convert Gmail credentials to EmailConfig.

        Args:
            email_address: Gmail address to use with these credentials

        Returns:
            EmailConfig configured for Gmail
        """
        return EmailConfig(
            email=email_address,
            password=self._credentials.get(
                "refresh_token", ""
            ),  # Use refresh token as password
            imap_server="imap.gmail.com",
            smtp_server="smtp.gmail.com",
            tls=True,
        )

    @property
    def client_id(self) -> str:
        """Get OAuth2 client ID."""
        return self._credentials.get("client_id", "")

    @property
    def client_secret(self) -> str:
        """Get OAuth2 client secret."""
        return self._credentials.get("client_secret", "")

    @property
    def refresh_token(self) -> str:
        """Get OAuth2 refresh token."""
        return self._credentials.get("refresh_token", "")

    @property
    def token_uri(self) -> str:
        """Get OAuth2 token URI."""
        return self._credentials.get("token_uri", "https://oauth2.googleapis.com/token")
