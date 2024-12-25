Email Clients
=============

.. module:: pymailai.base_client

The email client modules provide functionality for sending and receiving emails through different protocols and services.

BaseEmailClient
-------------

.. autoclass:: BaseEmailClient
   :members:
   :undoc-members:
   :show-inheritance:

   The BaseEmailClient class defines the interface for all email clients:

   - Abstract base class for email operations
   - Defines standard methods for email handling
   - Provides async context manager support

   Example of implementing a custom client:

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

IMAP/SMTP Client
--------------

.. module:: pymailai.client

.. autoclass:: EmailClient
   :members:
   :undoc-members:
   :show-inheritance:

   The EmailClient class provides IMAP/SMTP email operations with:

   - Improved SMTP connection handling with automatic reconnection
   - Comprehensive logging for debugging and monitoring
   - Support for Gmail OAuth2 authentication
   - Enhanced error handling for common email operations

   Example usage:

   .. code-block:: python

      from pymailai.client import EmailClient
      from pymailai.config import EmailConfig

      # Using standard IMAP/SMTP
      config = EmailConfig(
          imap_server="imap.gmail.com",
          smtp_server="smtp.gmail.com",
          email="your-email@gmail.com",
          password="your-password"
      )
      client = EmailClient(config)

      # Using OAuth2 credentials
      client = EmailClient.from_gmail_oauth2(
          email="your-email@gmail.com",
          credentials_path="~/.config/pymailai/gmail_creds.json"
      )

Gmail API Client
-------------

.. module:: pymailai.gmail_client

.. autoclass:: GmailClient
   :members:
   :undoc-members:
   :show-inheritance:

   The GmailClient class provides direct Gmail API access with:

   - Service account authentication support
   - Direct Gmail API operations
   - Enhanced message handling
   - Proper email threading

   Example usage with service account:

   .. code-block:: python

      from pymailai.gmail import ServiceAccountCredentials
      from pymailai.gmail_client import GmailClient

      # Set up service account
      creds = ServiceAccountCredentials(
          credentials_path="credentials.json",
          delegated_email="user@yourdomain.com",
          scopes=["https://www.googleapis.com/auth/gmail.modify"]
      )

      # Create Gmail client
      client = GmailClient(creds.get_gmail_service())

      # Use with EmailAgent
      agent = EmailAgent(client, message_handler=handler)

The client automatically handles connection management and authentication.
All operations are logged for debugging purposes.
