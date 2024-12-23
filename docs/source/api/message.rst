Message
=======

.. module:: pymailai.message

The message module provides classes for handling email messages with enhanced error handling and validation.

EmailMessage
-----------

.. autoclass:: EmailMessage
   :members:
   :undoc-members:
   :show-inheritance:

   The EmailMessage class represents an email message with improved error handling and validation:

   - Robust parsing of email headers and content
   - Support for multipart messages
   - Enhanced error handling for malformed messages
   - Validation of required fields

   Example usage:

   .. code-block:: python

      from pymailai.message import EmailMessage

      # Create a new message
      message = EmailMessage(
          subject="Hello",
          body="This is a test message",
          to="recipient@example.com",
          from_="sender@example.com"
      )

      # Access message parts
      print(message.subject)
      print(message.body)
      print(message.to)
      print(message.from_)
