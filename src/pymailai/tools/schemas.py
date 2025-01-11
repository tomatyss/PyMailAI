"""Email tool schemas for different AI model integrations."""

from typing import Dict, List


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
