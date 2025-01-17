"""Example of using PyMailAI with Ollama's chat API."""

import asyncio
import os
from typing import Optional

from ollama import chat, ChatResponse
from pymailai import EmailAgent, EmailConfig
from pymailai.message import EmailData


async def process_with_ollama(message: EmailData) -> Optional[EmailData]:
    """Process email content using Ollama's chat API.

    This example shows how to:
    1. Extract the prompt from an incoming email
    2. Send it to Ollama's API
    3. Send the response back via email
    """
    try:
        # Get completion from Ollama
        response: ChatResponse = chat(
            model="llama3.2",  # Latest Llama version
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": message.body_text,
                },
            ],
        )

        # Extract the response
        ai_response = response.message.content

        # Create email response
        return EmailData(
            message_id="",  # Will be generated by email server
            subject=f"Re: {message.subject}",
            from_address=message.to_addresses[0],  # Reply from the recipient
            to_addresses=[message.from_address],  # Reply to the sender
            cc_addresses=[],
            body_text=ai_response,
            body_html=None,
            timestamp=message.timestamp,
            in_reply_to=message.message_id,
            references=[message.message_id]
            if message.references is None
            else message.references + [message.message_id],
        )
    except Exception as e:
        print(f"Error processing message: {e}")
        return None


async def main():
    # Configure email settings - requires explicit server configuration
    config = EmailConfig(
        imap_server=os.getenv("IMAP_SERVER"),
        smtp_server=os.getenv("SMTP_SERVER"),
        email=os.getenv("EMAIL_ADDRESS"),
        password=os.getenv("EMAIL_PASSWORD"),
        smtp_port=int(os.getenv("SMTP_PORT", "465")),  # SSL/TLS port by default
        imap_port=int(os.getenv("IMAP_PORT", "993")),  # SSL/TLS port by default
    )

    # Create and run email agent
    async with EmailAgent(config, message_handler=process_with_ollama) as agent:
        print(f"Ollama Email Agent started. Monitoring {config.email}")
        print("Send an email to get an AI response!")
        print("Press Ctrl+C to stop...")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping email agent...")


if __name__ == "__main__":
    asyncio.run(main())
