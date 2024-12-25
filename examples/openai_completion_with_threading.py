"""Example of using PyMailAI with OpenAI's completion API and proper email threading."""

import asyncio
import os
from typing import Optional
from dotenv import load_dotenv

from openai import OpenAI
from pymailai import EmailAgent, EmailConfig
from pymailai.message import EmailData

# Load environment variables
load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


async def process_with_openai(message: EmailData) -> Optional[EmailData]:
    """Process email content using OpenAI's completion API.

    This example shows how to:
    1. Extract the prompt from an incoming email
    2. Send it to OpenAI's API
    3. Send the response back via email with proper threading
    """
    try:
        # Get completion from OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message.body_text}
            ]
        )

        # Extract the response
        ai_response = completion.choices[0].message.content

        # Create a properly threaded reply that includes the original message
        reply = message.create_reply(
            reply_text=ai_response,
            include_history=True  # This ensures the original message is quoted
        )

        # Set the from address since create_reply doesn't set it
        reply.from_address = message.to_addresses[0]

        return reply

    except Exception as e:
        print(f"Error processing message: {e}")
        return None


async def main():
    # Configure email settings
    config = EmailConfig(
        imap_server=os.getenv("IMAP_SERVER"),
        smtp_server=os.getenv("SMTP_SERVER"),
        email=os.getenv("EMAIL_ADDRESS"),
        password=os.getenv("EMAIL_PASSWORD"),
        smtp_port=465
    )

    # Create and run email agent
    async with EmailAgent(config, message_handler=process_with_openai) as agent:
        print(f"OpenAI Email Agent started. Monitoring {config.email}")
        print("Send an email to get an AI response with proper threading!")
        print("The response will include the original message and appear")
        print("properly threaded in your email client.")
        print("Press Ctrl+C to stop...")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping email agent...")

if __name__ == "__main__":
    asyncio.run(main())
