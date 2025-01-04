"""Tool definitions for AI model integration."""

from typing import Dict, List, Optional, Union

from pymailai.base_client import BaseEmailClient
from pymailai.message import EmailData


async def execute_query_emails(
    client: BaseEmailClient,
    after_date: Optional[str] = None,
    before_date: Optional[str] = None,
    subject: Optional[str] = None,
    from_address: Optional[str] = None,
    to_address: Optional[str] = None,
    label: Optional[str] = None,
    unread_only: Optional[bool] = None,
    include_body: Optional[bool] = None,
) -> List[Dict]:
    """Execute the query_emails tool using the provided email client.

    Args:
        client: Email client instance to use for querying
        after_date: Optional date to filter messages after (YYYY-MM-DD)
        before_date: Optional date to filter messages before (YYYY-MM-DD)
        subject: Optional subject line text to search for
        from_address: Optional sender email to filter by
        to_address: Optional recipient email to filter by
        label: Optional label/folder to search in
        unread_only: Optional flag to only return unread messages
        include_body: Optional flag to include message body content

    Returns:
        List of matching messages as dictionaries
    """
    try:
        query_params = {
            "after_date": after_date,
            "before_date": before_date,
            "subject": subject,
            "from_address": from_address,
            "to_address": to_address,
            "label": label,
            "unread_only": unread_only,
            "include_body": include_body,
        }

        # Remove None values
        query_params = {k: v for k, v in query_params.items() if v is not None}

        messages = []
        async for email in client.query_messages(query_params):
            messages.append(
                {
                    "id": email.message_id,
                    "subject": email.subject,
                    "from": email.from_address,
                    "to": email.to_addresses,
                    "cc": email.cc_addresses,
                    "date": email.timestamp.isoformat() if email.timestamp else None,
                    "body": email.body_text if include_body else None,
                    "unread": "UNREAD" in email.labels
                    if hasattr(email, "labels")
                    else None,
                }
            )

        return messages

    except Exception as e:
        return [{"error": str(e)}]


def get_email_tool_schema_anthropic() -> List[Dict]:
    """Get the email tool schema for Anthropic Claude models."""
    return [
        {
            "name": "send_email",
            "description": "Send an email message to specified recipients",
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of email addresses to send to",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (can include markdown formatting)",
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of CC recipients",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
        {
            "name": "query_emails",
            "description": "Search and retrieve emails based on specified criteria",
            "input_schema": {
                "type": "object",
                "properties": {
                    "after_date": {
                        "type": "string",
                        "description": "Return emails after this date (YYYY-MM-DD)",
                    },
                    "before_date": {
                        "type": "string",
                        "description": "Return emails before this date (YYYY-MM-DD)",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Search for emails with this text in subject",
                    },
                    "from_address": {
                        "type": "string",
                        "description": "Search for emails from this address",
                    },
                    "to_address": {
                        "type": "string",
                        "description": "Search for emails to this address",
                    },
                    "label": {
                        "type": "string",
                        "description": "Search for emails with this Gmail label",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only return unread emails if true",
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Include email body content in results",
                    },
                },
            },
        },
    ]


def get_email_tool_schema_openai() -> List[Dict]:
    """Get the email tool schema for OpenAI models."""
    return [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email message to specified recipients",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of email addresses to send to",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line",
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content (can include markdown formatting)",
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of CC recipients",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_emails",
                "description": "Search and retrieve emails based on specified criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "after_date": {
                            "type": "string",
                            "description": "Return emails after this date (YYYY-MM-DD)",
                        },
                        "before_date": {
                            "type": "string",
                            "description": "Return emails before this date (YYYY-MM-DD)",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Search for emails with this text in subject",
                        },
                        "from_address": {
                            "type": "string",
                            "description": "Search for emails from this address",
                        },
                        "to_address": {
                            "type": "string",
                            "description": "Search for emails to this address",
                        },
                        "label": {
                            "type": "string",
                            "description": "Search for emails with this Gmail label",
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "Only return unread emails if true",
                        },
                        "include_body": {
                            "type": "boolean",
                            "description": "Include email body content in results",
                        },
                    },
                },
            },
        },
    ]


def get_email_tool_schema_ollama() -> List[Dict]:
    """Get the email tool schema for Ollama models."""
    return [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email message to specified recipients",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of email addresses to send to",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line",
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content (can include markdown formatting)",
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of CC recipients",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_emails",
                "description": "Search and retrieve emails based on specified criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "after_date": {
                            "type": "string",
                            "description": "Return emails after this date (YYYY-MM-DD)",
                        },
                        "before_date": {
                            "type": "string",
                            "description": "Return emails before this date (YYYY-MM-DD)",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Search for emails with this text in subject",
                        },
                        "from_address": {
                            "type": "string",
                            "description": "Search for emails from this address",
                        },
                        "to_address": {
                            "type": "string",
                            "description": "Search for emails to this address",
                        },
                        "label": {
                            "type": "string",
                            "description": "Search for emails with this Gmail label",
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "Only return unread emails if true",
                        },
                        "include_body": {
                            "type": "boolean",
                            "description": "Include email body content in results",
                        },
                    },
                },
            },
        },
    ]


async def execute_send_email(
    client: "BaseEmailClient",
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
) -> Dict[str, Union[bool, str]]:
    """Execute the send_email tool using the provided email client.

    Args:
        client: Email client instance to use for sending
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body content
        cc: Optional list of CC recipients

    Returns:
        Dict containing success status and any error message
    """
    try:
        # Create EmailData instance
        email = EmailData(
            message_id="",  # Will be set by email server
            subject=subject,
            from_address="me",  # Will be replaced with authenticated user's address
            to_addresses=to,
            cc_addresses=cc or [],
            body_text=body,
        )

        # Send the email
        await client.send_message(email)

        return {"success": True, "error": ""}

    except Exception as e:
        return {"success": False, "error": str(e)}
