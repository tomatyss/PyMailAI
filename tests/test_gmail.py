"""Tests for Gmail credentials functionality."""

import json
import os
from pathlib import Path
import pytest
from unittest.mock import mock_open, patch

from pymailai.gmail import GmailCredentials


@pytest.fixture
def valid_creds_dict():
    """Fixture providing valid Gmail credentials dictionary."""
    return {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "type": "authorized_user"
    }


@pytest.fixture
def valid_creds_file(tmp_path, valid_creds_dict):
    """Fixture providing a temporary credentials file."""
    creds_file = tmp_path / "gmail_creds.json"
    with open(creds_file, 'w') as f:
        json.dump(valid_creds_dict, f)
    return creds_file


def test_load_credentials(valid_creds_file, valid_creds_dict):
    """Test loading credentials from a file."""
    creds = GmailCredentials(valid_creds_file)
    assert creds.client_id == valid_creds_dict["client_id"]
    assert creds.client_secret == valid_creds_dict["client_secret"]
    assert creds.refresh_token == valid_creds_dict["refresh_token"]
    assert creds.token_uri == valid_creds_dict["token_uri"]


def test_load_nonexistent_file():
    """Test error handling for nonexistent credentials file."""
    with pytest.raises(FileNotFoundError):
        GmailCredentials("nonexistent.json")


def test_load_invalid_json(tmp_path):
    """Test error handling for invalid JSON in credentials file."""
    invalid_file = tmp_path / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("not valid json")

    with pytest.raises(ValueError, match="Invalid JSON"):
        GmailCredentials(invalid_file)


def test_create_from_oauth_credentials(tmp_path):
    """Test creating credentials from OAuth2 details."""
    creds = GmailCredentials.from_oauth_credentials(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
        save_path=tmp_path / "new_creds.json"
    )

    assert creds.client_id == "test-client-id"
    assert creds.client_secret == "test-client-secret"
    assert creds.refresh_token == "test-refresh-token"
    assert creds.token_uri == "https://oauth2.googleapis.com/token"


def test_create_from_oauth_credentials_no_save():
    """Test creating credentials without saving to file."""
    test_creds = {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "type": "authorized_user"
    }

    with patch('builtins.open', mock_open(read_data=json.dumps(test_creds))) as mock_file:
        creds = GmailCredentials.from_oauth_credentials(
            client_id="test-client-id",
            client_secret="test-client-secret",
            refresh_token="test-refresh-token"
        )

        assert creds.client_id == "test-client-id"
        assert creds.client_secret == "test-client-secret"
        assert creds.refresh_token == "test-refresh-token"

        # Verify temp file was created and written to
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called()


def test_to_email_config(valid_creds_file):
    """Test converting credentials to EmailConfig."""
    creds = GmailCredentials(valid_creds_file)
    email = "test@gmail.com"
    config = creds.to_email_config(email)

    assert config.email == email
    assert config.password == creds.refresh_token
    assert config.imap_server == "imap.gmail.com"
    assert config.smtp_server == "smtp.gmail.com"
    assert config.tls is True


def test_missing_required_fields(tmp_path):
    """Test error handling for missing required fields in credentials."""
    incomplete_creds = {
        "client_id": "test-client-id",
        # Missing client_secret and refresh_token
    }

    creds_file = tmp_path / "incomplete_creds.json"
    with open(creds_file, 'w') as f:
        json.dump(incomplete_creds, f)

    creds = GmailCredentials(creds_file)
    assert creds.client_secret == ""  # Should return empty string for missing fields
    assert creds.refresh_token == ""


def test_custom_token_uri():
    """Test using a custom token URI."""
    custom_uri = "https://custom.example.com/token"
    creds = GmailCredentials.from_oauth_credentials(
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
        token_uri=custom_uri
    )

    assert creds.token_uri == custom_uri
