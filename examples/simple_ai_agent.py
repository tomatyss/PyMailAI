"""Example of using PyMailAI with a simple AI agent."""

import asyncio
import os
from typing import Optional

from pymailai import EmailAgent, EmailConfig
from pymailai.message import EmailData


async def ai_message_handler(message: EmailData) -> Optional[EmailData]:
    """Simple AI message handler that echoes back the received message.

    In a real application, this would integrate with an AI model to:
    1. Process the incoming message content
    2. Generate an appropriate response
    3. Format and return the response as a new EmailData object
    """
    # Create a reply using the helper method
    response = message.create_reply(
        reply_text=f"Received your message: {message.body_text}\n\nThis is an automated response."
    )
    return response


async def main():
    """Run the email agent with the AI message handler."""
    # Load configuration from environment variables
    config = EmailConfig(
        imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        email=os.getenv("EMAIL_ADDRESS"),
        password=os.getenv("EMAIL_PASSWORD")
    )

    # Validate configuration
    config.validate()

    # Create and run the email agent
    async with EmailAgent(config, message_handler=ai_message_handler) as agent:
        print(f"Email agent started. Monitoring {config.email}")
        print("Press Ctrl+C to stop...")

        try:
            # Keep the agent running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping email agent...")


if __name__ == "__main__":
    asyncio.run(main())
