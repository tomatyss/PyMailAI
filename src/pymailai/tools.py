"""Tool definitions for AI model integration."""

from typing import Dict, List, Optional, Union

from pymailai.base_client import BaseEmailClient
from pymailai.message import EmailData


def get_email_tool_schema_anthropic() -> Dict:
    """Get the email tool schema for Anthropic Claude models."""
    return {
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
    }


def get_email_tool_schema_openai() -> Dict:
    """Get the email tool schema for OpenAI models."""
    return {
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
    }


def get_email_tool_schema_ollama() -> Dict:
    """Get the email tool schema for Ollama models."""
    return {
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
    }


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
