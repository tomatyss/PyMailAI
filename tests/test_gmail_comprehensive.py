"""Comprehensive tests for Gmail OAuth functionality."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from google.auth import credentials

from pymailai.config import EmailConfig
from pymailai.gmail import (GmailCredentials, InvalidCredentialsError,
                          create_from_oauth_credentials, load_credentials)


class MockCredentials(credentials.Credentials):
    """Mock credentials class for testing."""
    def __init__(self, *args, **kwargs):
        pass

    def refresh(self, request):
        pass


class MockInvalidCredentials(credentials.Credentials):
    """Mock credentials class that raises an error."""
    def __init__(self, *args, **kwargs):
        raise ValueError("Invalid creds")

    def refresh(self, request):
        pass


@pytest.fixture
def oauth_creds():
    """Create test OAuth credentials."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "refresh_token": "test_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.modify"],
    }


@pytest.fixture
def gmail_creds(oauth_creds):
    """Create test Gmail credentials."""
    return GmailCredentials(
        client_id=oauth_creds["client_id"],
        client_secret=oauth_creds["client_secret"],
        refresh_token=oauth_creds["refresh_token"],
        token_uri=oauth_creds["token_uri"],
        scopes=oauth_creds["scopes"],
    )


def test_load_credentials_success(oauth_creds):
    """Test successful loading of credentials from file."""
    mock_file = mock_open(read_data=json.dumps(oauth_creds))

    with patch("builtins.open", mock_file):
        creds = load_credentials("fake_path.json")

    assert creds.client_id == oauth_creds["client_id"]
    assert creds.client_secret == oauth_creds["client_secret"]
    assert creds.refresh_token == oauth_creds["refresh_token"]
    assert creds.token_uri == oauth_creds["token_uri"]
    assert creds.scopes == oauth_creds["scopes"]


def test_load_credentials_file_not_found():
    """Test handling of non-existent credentials file."""
    with pytest.raises(FileNotFoundError):
        load_credentials("nonexistent.json")


def test_load_credentials_invalid_json():
    """Test handling of invalid JSON in credentials file."""
    mock_file = mock_open(read_data="invalid json")

    with patch("builtins.open", mock_file), \
         pytest.raises(InvalidCredentialsError):
        load_credentials("fake_path.json")


def test_load_credentials_missing_fields(oauth_creds):
    """Test handling of missing required fields in credentials."""
    del oauth_creds["client_id"]
    mock_file = mock_open(read_data=json.dumps(oauth_creds))

    with patch("builtins.open", mock_file), \
         pytest.raises(InvalidCredentialsError):
        load_credentials("fake_path.json")


def test_create_from_oauth_with_save(oauth_creds, tmp_path):
    """Test creating credentials from OAuth with saving to file."""
    creds_path = tmp_path / "creds.json"

    with patch("google.oauth2.credentials.Credentials", MockCredentials):
        creds = create_from_oauth_credentials(
            oauth_creds,
            save_path=str(creds_path)
        )

    assert creds.client_id == oauth_creds["client_id"]
    assert creds.client_secret == oauth_creds["client_secret"]
    assert creds.refresh_token == oauth_creds["refresh_token"]
    assert os.path.exists(creds_path)


def test_create_from_oauth_without_save(oauth_creds):
    """Test creating credentials from OAuth without saving."""
    with patch("google.oauth2.credentials.Credentials", MockCredentials):
        creds = create_from_oauth_credentials(oauth_creds)

    assert creds.client_id == oauth_creds["client_id"]
    assert creds.client_secret == oauth_creds["client_secret"]
    assert creds.refresh_token == oauth_creds["refresh_token"]


def test_create_from_oauth_invalid_creds(oauth_creds):
    """Test handling of invalid OAuth credentials."""
    with patch("google.oauth2.credentials.Credentials", MockInvalidCredentials), \
         pytest.raises(InvalidCredentialsError):
        create_from_oauth_credentials(oauth_creds)


def test_gmail_credentials_to_oauth(gmail_creds):
    """Test converting GmailCredentials to OAuth2 credentials."""
    with patch("google.oauth2.credentials.Credentials", MockCredentials):
        oauth_creds = gmail_creds.to_oauth_credentials()

    assert isinstance(oauth_creds, MockCredentials)


def test_gmail_credentials_to_email_config(gmail_creds):
    """Test converting GmailCredentials to EmailConfig."""
    config = gmail_creds.to_email_config()

    assert isinstance(config, EmailConfig)
    assert config.email == (gmail_creds.email or "")
    assert config.password == gmail_creds.refresh_token
    assert config.imap_server == "imap.gmail.com"
    assert config.smtp_server == "smtp.gmail.com"
    assert config.imap_port == 993
    assert config.smtp_port == 587
    assert config.tls is True


def test_gmail_credentials_custom_token_uri(oauth_creds):
    """Test GmailCredentials with custom token URI."""
    custom_uri = "https://custom.token.uri"
    oauth_creds["token_uri"] = custom_uri

    creds = GmailCredentials(**oauth_creds)
    assert creds.token_uri == custom_uri


def test_gmail_credentials_default_scopes(oauth_creds):
    """Test GmailCredentials default scopes."""
    del oauth_creds["scopes"]

    creds = GmailCredentials(
        client_id=oauth_creds["client_id"],
        client_secret=oauth_creds["client_secret"],
        refresh_token=oauth_creds["refresh_token"],
    )
    assert "https://www.googleapis.com/auth/gmail.modify" in creds.scopes


def test_gmail_credentials_custom_scopes(oauth_creds):
    """Test GmailCredentials with custom scopes."""
    custom_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    oauth_creds["scopes"] = custom_scopes

    creds = GmailCredentials(**oauth_creds)
    assert creds.scopes == custom_scopes


def test_gmail_credentials_validation(oauth_creds):
    """Test GmailCredentials validation."""
    # Test required fields
    required_fields = ["client_id", "client_secret", "refresh_token"]
    for field in required_fields:
        invalid_creds = oauth_creds.copy()
        del invalid_creds[field]

        with pytest.raises(InvalidCredentialsError):
            GmailCredentials(
                client_id=invalid_creds.get("client_id", ""),
                client_secret=invalid_creds.get("client_secret", ""),
                refresh_token=invalid_creds.get("refresh_token", ""),
            )

    # Test empty values
    for field in required_fields:
        invalid_creds = oauth_creds.copy()
        invalid_creds[field] = ""

        with pytest.raises(InvalidCredentialsError):
            GmailCredentials(
                client_id=invalid_creds["client_id"],
                client_secret=invalid_creds["client_secret"],
                refresh_token=invalid_creds["refresh_token"],
            )


def test_gmail_credentials_str_repr(gmail_creds):
    """Test string representation of GmailCredentials."""
    str_rep = str(gmail_creds)

    assert gmail_creds.client_id in str_rep
    assert gmail_creds.client_secret not in str_rep  # Should not expose secret
    assert gmail_creds.refresh_token not in str_rep  # Should not expose token
