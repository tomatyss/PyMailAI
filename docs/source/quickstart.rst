Quick Start Guide
================

This guide will help you get started with pymailai quickly.

Installation
-----------

Install pymailai with pip:

.. code-block:: bash

   pip install pymailai

Basic Usage
----------

Here's a simple example of creating an email agent that processes incoming emails:

.. code-block:: python

   import asyncio
   import os
   from typing import Optional

   from pymailai import EmailAgent, EmailConfig
   from pymailai.message import EmailData

   async def message_handler(message: EmailData) -> Optional[EmailData]:
       """Process incoming emails and generate responses."""
       # Create a reply using the helper method
       return message.create_reply(
           reply_text=f"Received your message: {message.body_text}"
       )

   async def main():
       # Configure email settings
       config = EmailConfig(
           imap_server=os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com"),
           smtp_server=os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
           email=os.getenv("EMAIL_ADDRESS"),
           password=os.getenv("EMAIL_PASSWORD")
       )

       # Create and run email agent
       async with EmailAgent(config, message_handler=message_handler) as agent:
           print(f"Email agent started. Monitoring {config.email}")
           print("Press Ctrl+C to stop...")

           try:
               while True:
                   await asyncio.sleep(1)
           except KeyboardInterrupt:
               print("\nStopping email agent...")

   if __name__ == "__main__":
       asyncio.run(main())

Gmail Authentication
------------------

pymailai supports two methods for Gmail authentication:

1. OAuth2 (for personal Gmail accounts)
2. Service Account (for Google Workspace accounts)

OAuth2 Setup (Personal Gmail)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For personal Gmail accounts, OAuth2 authentication is recommended:

1. Install with Gmail support:

   .. code-block:: bash

      pip install pymailai[gmail]

2. Set up Google Cloud Project:

   a. Go to the `Google Cloud Console <https://console.cloud.google.com/>`_
   b. Create a new project or select an existing one
   c. Enable the Gmail API
   d. Create OAuth2 credentials (Desktop application type)
   e. Download the credentials

3. Get refresh token using the helper script:

   .. code-block:: bash

      # Set required environment variables
      export GMAIL_CLIENT_ID="your-client-id"
      export GMAIL_CLIENT_SECRET="your-client-secret"

      # Run the helper script
      python examples/get_gmail_token.py

4. Use Gmail credentials in your code:

.. code-block:: python

   from pathlib import Path
   from pymailai import EmailAgent
   from pymailai.gmail import GmailCredentials

   async def main():
       # Load Gmail credentials
       creds_path = Path.home() / ".config" / "pymailai" / "gmail_creds.json"
       creds = GmailCredentials(creds_path)

       # Convert to EmailConfig
       config = creds.to_email_config("your-email@gmail.com")

       # Create and run agent
       async with EmailAgent(config, message_handler=message_handler) as agent:
           # ... rest of the code ...

Service Account Setup (Google Workspace)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Google Workspace accounts, service account authentication provides better security and control:

1. Set up Google Cloud Project:

   a. Go to the `Google Cloud Console <https://console.cloud.google.com/>`_
   b. Create a new project or select an existing one
   c. Enable the Gmail API
   d. Create a service account
   e. Download the service account JSON key file

2. Configure Google Workspace:

   a. Go to Admin Console -> Security -> API Controls
   b. Under "Domain-wide Delegation", add your service account
   c. Add the required scope: ``https://www.googleapis.com/auth/gmail.modify``

3. Use service account in your code:

.. code-block:: python

   import asyncio
   from pymailai import EmailAgent
   from pymailai.gmail import ServiceAccountCredentials
   from pymailai.gmail_client import GmailClient

   async def main():
       # Set up service account authentication
       creds = ServiceAccountCredentials(
           credentials_path="credentials.json",
           delegated_email="user@yourdomain.com",
           scopes=["https://www.googleapis.com/auth/gmail.modify"]
       )

       # Create Gmail client
       client = GmailClient(creds.get_gmail_service())

       # Create and run agent
       async with EmailAgent(client, message_handler=message_handler) as agent:
           # ... rest of the code ...

Custom Email Clients
-----------------

pymailai provides a BaseEmailClient interface for implementing custom email clients:

.. code-block:: python

   from pymailai.base_client import BaseEmailClient
   from pymailai.message import EmailData

   class MyCustomClient(BaseEmailClient):
       async def connect(self) -> None:
           # Connect to email service
           pass

       async def disconnect(self) -> None:
           # Disconnect from service
           pass

       async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
           # Fetch new messages
           pass

       async def send_message(self, message: EmailData) -> None:
           # Send a message
           pass

       async def mark_as_read(self, message_id: str) -> None:
           # Mark message as read
           pass

AI Integration
-------------

pymailai supports integration with various AI providers:

OpenAI Example
~~~~~~~~~~~~~

.. code-block:: bash

   pip install pymailai[openai]

.. code-block:: python

   import os
   from openai import OpenAI
   from pymailai import EmailAgent, EmailConfig
   from pymailai.message import EmailData

   client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

   async def process_with_openai(message: EmailData) -> Optional[EmailData]:
       completion = client.chat.completions.create(
           model="gpt-4",
           messages=[
               {"role": "system", "content": "You are a helpful assistant."},
               {"role": "user", "content": message.body_text}
           ]
       )

       # Create reply using the helper method
       return message.create_reply(
           reply_text=completion.choices[0].message.content
       )

Anthropic Example
~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install pymailai[anthropic]

.. code-block:: python

   import anthropic
   from pymailai import EmailAgent, EmailConfig
   from pymailai.message import EmailData

   client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

   async def process_with_anthropic(message: EmailData) -> Optional[EmailData]:
       message_content = await client.messages.create(
           model="claude-3-opus-20240229",
           max_tokens=1024,
           messages=[
               {"role": "user", "content": message.body_text}
           ]
       )

       # Create reply using the helper method
       return message.create_reply(
           reply_text=message_content.content[0].text
       )

Ollama Example
~~~~~~~~~~~~

.. code-block:: bash

   pip install pymailai[ollama]

.. code-block:: python

   from ollama import chat, ChatResponse
   from pymailai import EmailAgent, EmailConfig
   from pymailai.message import EmailData

   async def process_with_ollama(message: EmailData) -> Optional[EmailData]:
       response: ChatResponse = chat(
           model="llama3.2",  # Latest Llama version
           messages=[
               {"role": "system", "content": "You are a helpful assistant."},
               {"role": "user", "content": message.body_text}
           ]
       )

       # Create reply using the helper method
       return message.create_reply(
           reply_text=response.message.content
       )

Next Steps
---------

- Check out the :doc:`examples` for more detailed examples
- Read the :doc:`api/index` for detailed API documentation
- Learn about :doc:`api/client` for advanced email client features
