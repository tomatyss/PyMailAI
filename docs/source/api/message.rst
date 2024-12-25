Message
=======

.. module:: pymailai.message

The message module provides classes for handling email messages, with support for threading, attachments, and HTML content.

EmailData
---------

.. autoclass:: EmailData
   :members:
   :undoc-members:
   :show-inheritance:

   The EmailData class represents an email message with comprehensive support for:

   - Email threading and conversation history
   - Multipart messages (text/html)
   - File attachments
   - Message metadata (references, in-reply-to)
   - Enhanced error handling and validation

   Example usage:

   .. code-block:: python

      from pymailai.message import EmailData
      from datetime import datetime

      # Create a new message
      message = EmailData(
          message_id="",  # Will be set by email server
          subject="Hello",
          from_address="sender@example.com",
          to_addresses=["recipient@example.com"],
          cc_addresses=[],
          body_text="This is a test message",
          body_html=None,  # Optional HTML version
          timestamp=datetime.now()
      )

      # Create a threaded reply
      reply = message.create_reply(
          reply_text="Thanks for your message!",
          include_history=True  # Include quoted original
      )
      reply.from_address = "recipient@example.com"

   Key Methods
   ~~~~~~~~~~

   create_reply(reply_text, include_history=True, quote_level=1)
      Create a properly threaded reply to this message.

      - Includes the original message as quoted text (if include_history=True)
      - Sets correct threading metadata (References and In-Reply-To headers)
      - Maintains CC recipients
      - Supports nested reply quotation levels

      Args:
          reply_text (str): The text of the reply message
          include_history (bool): Whether to include quoted message history
          quote_level (int): The quotation level for the previous message

      Returns:
          EmailData: A new EmailData object configured as a reply

   from_email_message(msg)
      Create EmailData from an email.message.EmailMessage object.

      Handles:

      - Multipart message parsing
      - Attachment extraction
      - Header processing
      - Threading metadata

   to_email_message()
      Convert EmailData to an email.message.EmailMessage object.

      Handles:

      - Markdown to HTML conversion
      - Multipart message creation
      - Attachment packaging
      - Header generation

   Threading Fields
   ~~~~~~~~~~~~~

   - message_id: Unique identifier for the message
   - in_reply_to: Message ID this is replying to
   - references: List of ancestor message IDs in the thread
