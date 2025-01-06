"""Tool definitions for AI model integration."""

from pymailai.tools.core import execute_query_emails, execute_send_email
from pymailai.tools.schemas import (
    get_email_tool_schema_anthropic,
    get_email_tool_schema_ollama,
    get_email_tool_schema_openai,
)

__all__ = [
    "execute_query_emails",
    "execute_send_email",
    "get_email_tool_schema_anthropic",
    "get_email_tool_schema_ollama",
    "get_email_tool_schema_openai",
]
