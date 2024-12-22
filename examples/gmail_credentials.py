"""Example of using PyMailAI with Gmail credentials from a file."""

import asyncio
import os
from pathlib import Path

from pymailai import EmailAgent
from pymailai.gmail import GmailCredentials
from pymailai.message import EmailData

async def echo_handler(message: EmailData) -> EmailData:
    """Simple echo handler that replies with the received message."""
    return EmailData(
        message_id="",
        subject=f"Re: {message.subject}",
        from_address=message.to_addresses[0],
        to_addresses=[message.from_address],
        cc_addresses=[],
        body_text=f"Received your message:\n\n{message.body_text}",
        body_html=None,
        timestamp=message.timestamp,
        in_reply_to=message.message_id,
        references=[message.message_id]
    )

async def main():
    # Load Gmail credentials from file
    creds_path = Path.home() / ".config" / "pymailai" / "gmail_creds.json"

    # If credentials file doesn't exist, create it from environment variables
    if not creds_path.exists():
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        creds = GmailCredentials.from_oauth_credentials(
            client_id=os.getenv("GMAIL_CLIENT_ID", ""),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            refresh_token=os.getenv("GMAIL_REFRESH_TOKEN", ""),
            save_path=creds_path
        )
    else:
        creds = GmailCredentials(creds_path)

    # Convert to EmailConfig
    email_address = os.getenv("GMAIL_ADDRESS", "")
    config = creds.to_email_config(email_address)

    # Create and run email agent
    async with EmailAgent(config, message_handler=echo_handler) as agent:
        print(f"Gmail Agent started. Monitoring {config.email}")
        print("Send an email to get an echo response!")
        print("Press Ctrl+C to stop...")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping email agent...")

if __name__ == "__main__":
    asyncio.run(main())
