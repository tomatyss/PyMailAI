"""Example of using PyMailAI with Anthropic's Claude API."""

import asyncio
import os
from typing import Optional

import anthropic
from pymailai import EmailAgent, EmailConfig
from pymailai.message import EmailData

# Configure Anthropic client
client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def process_with_anthropic(message: EmailData) -> Optional[EmailData]:
    """Process email content using Anthropic's Claude API.

    This example shows how to:
    1. Extract the prompt from an incoming email
    2. Send it to Anthropic's API
    3. Send the response back via email
    """
    try:
        # Get completion from Anthropic
        message_content = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": message.body_text}
            ]
        )

        # Extract the response
        ai_response = message_content.content[0].text

        # Create email response
        return EmailData(
            message_id="",  # Will be generated by email server
            subject=f"Re: {message.subject}",
            from_address=message.to_addresses[0],  # Reply from the recipient
            to_addresses=[message.from_address],   # Reply to the sender
            cc_addresses=[],
            body_text=ai_response,
            body_html=None,
            timestamp=message.timestamp,
            in_reply_to=message.message_id,
            references=[message.message_id] if message.references is None
                      else message.references + [message.message_id]
        )
    except Exception as e:
        print(f"Error processing message: {e}")
        return None

async def main():
    # Configure email settings
    config = EmailConfig(
        imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        email=os.getenv("EMAIL_ADDRESS"),
        password=os.getenv("EMAIL_PASSWORD")
    )

    # Create and run email agent
    async with EmailAgent(config, message_handler=process_with_anthropic) as agent:
        print(f"Anthropic Email Agent started. Monitoring {config.email}")
        print("Send an email to get an AI response!")
        print("Press Ctrl+C to stop...")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping email agent...")

if __name__ == "__main__":
    asyncio.run(main())
