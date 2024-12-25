"""Gmail credential handling for PyMailAI."""

import base64
import json
import logging
from dataclasses import dataclass
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import EmailConfig


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid or missing required fields."""

    pass


class GmailAPIError(Exception):
    """Raised when Gmail API operations fail."""

    pass


@dataclass
class ServiceAccountCredentials:
    """Gmail service account credentials."""

    credentials_path: str
    delegated_email: str
    scopes: Optional[List[str]] = None

    def __post_init__(self):
        """Validate and set default scopes."""
        if not self.credentials_path or not self.delegated_email:
            raise InvalidCredentialsError("Missing required credential fields")

        if self.scopes is None:
            self.scopes = ["https://www.googleapis.com/auth/gmail.modify"]

    def to_credentials(
        self,
    ) -> (
        Any
    ):  # Type Any since google.oauth2.service_account.Credentials type is dynamic
        """Convert to Google service account credentials."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=self.scopes
            )
            return credentials.with_subject(self.delegated_email)
        except Exception as e:
            raise InvalidCredentialsError(f"Invalid service account credentials: {e}")

    def get_gmail_service(
        self,
    ) -> Any:  # Type Any since googleapiclient.discovery.build return type is dynamic
        """Get an authenticated Gmail API service."""
        try:
            credentials = self.to_credentials()
            return build("gmail", "v1", credentials=credentials)
        except Exception as e:
            raise GmailAPIError(f"Failed to create Gmail service: {e}")


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


def load_credentials(
    path: Union[str, Path]
) -> Union[GmailCredentials, ServiceAccountCredentials]:
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
        # Check if this is a service account credentials file
        if data.get("type") == "service_account":
            return ServiceAccountCredentials(
                credentials_path=str(path),
                delegated_email=data.get("delegated_email", ""),
                scopes=data.get("scopes"),
            )
        # Otherwise treat as OAuth credentials
        return GmailCredentials(**data)
    except (TypeError, ValueError) as e:
        raise InvalidCredentialsError(f"Invalid credentials format: {e}")


def encode_base64_data(data: str) -> str:
    """Encode data as URL-safe base64."""
    return base64.urlsafe_b64encode(data.encode()).decode()


def decode_base64_data(data: str) -> str:
    """Decode URL-safe base64 data."""
    return base64.urlsafe_b64decode(data).decode()


def get_email_content(service: Any, message_id: str) -> Dict[str, Any]:
    """Get the content of an email and its attachments."""
    try:
        msg = service.users().messages().get(userId="me", id=message_id).execute()
        payload = msg["payload"]
        parts = payload.get("parts", [])

        email_content: Dict[str, Any] = {
            "text": "",
            "html": "",
            "attachments": [],  # List[Dict[str, str]]
        }

        def extract_parts(parts):
            for part in parts:
                mime_type = part.get("mimeType")
                if mime_type == "text/plain":
                    body_data = part["body"].get("data")
                    if body_data:
                        email_content["text"] = decode_base64_data(body_data)
                elif mime_type == "text/html":
                    body_data = part["body"].get("data")
                    if body_data:
                        email_content["html"] = decode_base64_data(body_data)
                elif part.get("filename"):  # This part is an attachment
                    attachment_id = part["body"].get("attachmentId")
                    if attachment_id:
                        attachment = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(userId="me", messageId=message_id, id=attachment_id)
                            .execute()
                        )
                        attachment_data = attachment.get("data")
                        if attachment_data:
                            email_content["attachments"].append(
                                {
                                    "filename": part["filename"],
                                    "data": attachment_data,
                                    "mime_type": mime_type,
                                }
                            )
                elif part.get("parts"):  # Handle nested parts
                    extract_parts(part["parts"])

        if not parts:  # Single part email
            body_data = payload["body"].get("data")
            if payload["mimeType"] == "text/plain" and body_data:
                email_content["text"] = decode_base64_data(body_data)
            elif payload["mimeType"] == "text/html" and body_data:
                email_content["html"] = decode_base64_data(body_data)
        else:  # Multipart email
            extract_parts(parts)

        return email_content
    except HttpError as error:
        raise GmailAPIError(f"Failed to get email content: {error}")


def send_email(
    service: Any,
    to: str,
    subject: str,
    message_text: str,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Send an email using the Gmail API."""
    try:
        mime_message = MIMEText(message_text, "html")
        mime_message["to"] = to
        mime_message["subject"] = subject
        if in_reply_to:
            mime_message["In-Reply-To"] = in_reply_to
        if references:
            mime_message["References"] = references

        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        body = {"raw": raw}

        sent_message: Dict[str, Any] = (
            service.users().messages().send(userId="me", body=body).execute()
        )
        logging.info(f"Message Id: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        logging.error(f"An error occurred: {error}")
        raise GmailAPIError(f"Failed to send email: {error}")


def get_or_create_label(service: Any, label_name: str) -> Optional[str]:
    """Get or create a Gmail label."""
    try:
        # Extract only the email part if the label_name contains a name
        if "<" in label_name and ">" in label_name:
            label_name = label_name.split("<")[1].split(">")[0].strip()

        labels = service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"] == label_name:
                logging.info(f"Label '{label_name}' found with ID: {label['id']}")
                return str(label["id"])

        # Label not found, create it
        label = {
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
            "name": label_name,
        }
        created_label = (
            service.users().labels().create(userId="me", body=label).execute()
        )
        logging.info(f"Label '{label_name}' created with ID: {created_label['id']}")
        return str(created_label["id"])
    except HttpError as error:
        logging.error(f"An error occurred while getting or creating label: {error}")
        raise GmailAPIError(f"Failed to get or create label: {error}")


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
