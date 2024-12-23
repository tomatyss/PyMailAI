"""Tests for Gmail OAuth functionality."""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from pymailai.config import EmailConfig
from pymailai.gmail import (GmailCredentials, InvalidCredentialsError,
                          create_from_oauth_credentials, load_credentials)


@pytest.fixture
def valid_creds_dict():
    """Create valid test credentials."""
    return {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/gmail.modify"],
    }


@pytest.fixture
def valid_creds_file(tmp_path, valid_creds_dict):
    """Create a valid credentials file."""
    creds_file = tmp_path / "gmail_creds.json"
    with open(creds_file, "w") as f:
        json.dump(valid_creds_dict, f)
    return creds_file


def test_load_credentials(valid_creds_file, valid_creds_dict):
    """Test loading credentials from a file."""
    creds = load_credentials(valid_creds_file)

    assert creds.client_id == valid_creds_dict["client_id"]
    assert creds.client_secret == valid_creds_dict["client_secret"]
    assert creds.refresh_token == valid_creds_dict["refresh_token"]
    assert creds.token_uri == valid_creds_dict["token_uri"]
    assert creds.scopes == valid_creds_dict["scopes"]


def test_load_nonexistent_file():
    """Test error handling for nonexistent credentials file."""
    with pytest.raises(FileNotFoundError):
        load_credentials("nonexistent.json")


def test_load_invalid_json(tmp_path):
    """Test error handling for invalid JSON in credentials file."""
    invalid_file = tmp_path / "invalid.json"
    with open(invalid_file, "w") as f:
        f.write("not valid json")

    with pytest.raises(InvalidCredentialsError, match="Invalid JSON"):
        load_credentials(invalid_file)


def test_create_from_oauth_credentials(tmp_path):
    """Test creating credentials from OAuth2 details."""
    creds = create_from_oauth_credentials(
        {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "refresh_token": "test-refresh-token",
        },
        save_path=tmp_path / "new_creds.json",
    )

    assert creds.client_id == "test-client-id"
    assert creds.client_secret == "test-client-secret"
    assert creds.refresh_token == "test-refresh-token"


def test_create_from_oauth_credentials_no_save():
    """Test creating credentials without saving to file."""
    test_creds = {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "type": "authorized_user",
    }

    creds = create_from_oauth_credentials(test_creds)

    assert creds.client_id == "test-client-id"
    assert creds.client_secret == "test-client-secret"
    assert creds.refresh_token == "test-refresh-token"


def test_to_email_config(valid_creds_dict):
    """Test converting credentials to EmailConfig."""
    creds = GmailCredentials(**valid_creds_dict)
    config = creds.to_email_config()

    assert isinstance(config, EmailConfig)
    assert config.email == ""  # No email provided
    assert config.password == creds.refresh_token
    assert config.imap_server == "imap.gmail.com"
    assert config.smtp_server == "smtp.gmail.com"
    assert config.imap_port == 993
    assert config.smtp_port == 587
    assert config.tls is True


def test_missing_required_fields():
    """Test error handling for missing required fields in credentials."""
    with pytest.raises(InvalidCredentialsError):
        GmailCredentials(
            client_id="test-client-id",
            client_secret="",  # Empty secret
            refresh_token="test-refresh-token",
        )


def test_custom_token_uri():
    """Test using a custom token URI."""
    custom_uri = "https://custom.example.com/token"
    creds = GmailCredentials(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
        token_uri=custom_uri,
    )
    assert creds.token_uri == custom_uri
