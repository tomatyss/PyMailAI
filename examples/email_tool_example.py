"""Example of using email sending tool with AI models."""

import asyncio
import os
from typing import Dict, List

import anthropic
import ollama
from openai import OpenAI

from pymailai.gmail import create_gmail_client
from pymailai.tools import (
    execute_send_email,
    get_email_tool_schema_anthropic,
    get_email_tool_schema_ollama,
    get_email_tool_schema_openai,
)


async def example_anthropic() -> None:
    """Example using email tool with Anthropic Claude."""
    # Initialize Gmail client
    gmail = await create_gmail_client()

    # Initialize Anthropic client
    client = anthropic.Anthropic()

    # Create message with email tool
    response = await client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        tools=[get_email_tool_schema_anthropic()],
        messages=[
            {
                "role": "user",
                "content": "Please send an email to test@example.com with the subject 'Test Email' and body 'This is a test email sent via AI'",
            }
        ],
    )

    # Process tool calls
    for tool_call in response.content[0].tool_calls or []:
        if tool_call.name == "send_email":
            args = tool_call.parameters
            result = await execute_send_email(
                gmail,
                to=args["to"],
                subject=args["subject"],
                body=args["body"],
                cc=args.get("cc"),
            )
            print(f"Email send result: {result}")


async def example_openai() -> None:
    """Example using email tool with OpenAI GPT."""
    # Initialize Gmail client
    gmail = await create_gmail_client()

    # Initialize OpenAI client
    client = OpenAI()

    # Create chat completion with email tool
    completion = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": "Please send an email to test@example.com with the subject 'Test Email' and body 'This is a test email sent via AI'",
            }
        ],
        tools=[get_email_tool_schema_openai()],
    )

    # Process tool calls
    for tool_call in completion.choices[0].message.tool_calls or []:
        if tool_call.function.name == "send_email":
            args = tool_call.function.arguments
            result = await execute_send_email(
                gmail,
                to=args["to"],
                subject=args["subject"],
                body=args["body"],
                cc=args.get("cc"),
            )
            print(f"Email send result: {result}")


async def example_ollama() -> None:
    """Example using email tool with Ollama."""
    # Initialize Gmail client
    gmail = await create_gmail_client()

    # Create chat completion with email tool
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {
                "role": "user",
                "content": "Please send an email to test@example.com with the subject 'Test Email' and body 'This is a test email sent via AI'",
            }
        ],
        tools=[get_email_tool_schema_ollama()],
    )

    # Process tool calls
    for tool_call in response["message"].get("tool_calls", []):
        if tool_call["function"]["name"] == "send_email":
            args = tool_call["function"]["arguments"]
            result = await execute_send_email(
                gmail,
                to=args["to"],
                subject=args["subject"],
                body=args["body"],
                cc=args.get("cc"),
            )
            print(f"Email send result: {result}")


if __name__ == "__main__":
    asyncio.run(example_anthropic())
    # Or run other examples:
    # asyncio.run(example_openai())
    # asyncio.run(example_ollama())
