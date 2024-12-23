Email Client
============

.. module:: pymailai.client

The email client module provides functionality for sending and receiving emails with enhanced SMTP connection handling and logging.

EmailClient
----------

.. autoclass:: EmailClient
   :members:
   :undoc-members:
   :show-inheritance:

   The EmailClient class provides a robust interface for email operations with:

   - Improved SMTP connection handling with automatic reconnection
   - Comprehensive logging for debugging and monitoring
   - Support for Gmail OAuth2 authentication
   - Enhanced error handling for common email operations

   Example usage with Gmail OAuth2:

   .. code-block:: python

      from pymailai.client import EmailClient

      # Using OAuth2 credentials
      client = EmailClient.from_gmail_oauth2(
          email="your-email@gmail.com",
          credentials_path="~/.config/pymailai/gmail_creds.json"
      )

      # Using environment variables
      client = EmailClient.from_env()

   The client automatically handles connection management and will reconnect if the connection is lost.
   All operations are logged for debugging purposes.
