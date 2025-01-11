"""Example of processing emails with a specific label using AI.

This script demonstrates how to:
1. Query emails with a specific label (e.g. "todo")
2. Process those emails with Claude AI to extract todo items
3. Send a summary email with the extracted todos

To use this script:

1. Set up environment variables:
   export ANTHROPIC_API_KEY="your-api-key"
   export USER_EMAIL="your-email@example.com"

2. Label important emails with "todo" in Gmail

3. Run the script:
   python examples/todo_label_processor.py

4. To run it every morning, you can use cron:
   0 8 * * * cd /path/to/pymailai && python examples/todo_label_processor.py

The script will check for any emails labeled "todo" from the last 24 hours,
analyze them with AI to extract actionable items, and send you a summary email.
"""

import asyncio
import os
from datetime import datetime
from typing import List

import anthropic
from pymailai.agent import Agent
from pymailai.gmail import create_gmail_client
from pymailai.message import EmailData
from pymailai.tools import execute_send_email

async def process_todo_emails() -> None:
    """Process emails with 'todo' label and send a summary."""
    # Initialize Gmail client
    gmail = await create_gmail_client()

    # Initialize Anthropic client for AI processing
    client = anthropic.Anthropic()

    # Query emails with 'todo' label from the last 24 hours
    today = datetime.now().strftime("%Y/%m/%d")
    todo_emails: List[EmailData] = []

    async for email in gmail.query_messages({
        "label": "todo",
        "after_date": today,
        "include_body": True
    }):
        todo_emails.append(email)

    if not todo_emails:
        print("No todo emails found for today")
        return

    # Process emails with AI to generate summary
    todos = []
    for email in todo_emails:
        # Create message for AI to analyze the email
        response = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Analyze this email and extract the key todo items and their context:
                Subject: {email.subject}
                From: {email.from_address}
                Body: {email.body_text}

                Format each todo item as a bullet point with any relevant details."""
            }]
        )

        todos.append(response.content[0].text)

    # Generate summary email
    summary = "\n\n".join([
        "Here are your todo items from labeled emails:",
        *todos,
        "\nThis summary was automatically generated from emails labeled 'todo' in your inbox."
    ])

    # Get user's email address from environment
    user_email = os.environ.get("USER_EMAIL")
    if not user_email:
        raise ValueError("USER_EMAIL environment variable not set")

    # Send summary email
    await execute_send_email(
        gmail,
        to=user_email,
        subject=f"Todo Summary for {today}",
        body=summary
    )

    print(f"Sent todo summary to {user_email}")

if __name__ == "__main__":
    asyncio.run(process_todo_emails())
