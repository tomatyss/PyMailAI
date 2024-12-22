Configuration
============

The EmailConfig class handles all configuration settings for email server connections and processing behavior.

.. autoclass:: pymailai.config.EmailConfig
   :members:
   :show-inheritance:

Configuration Parameters
----------------------

- **imap_server** (str): IMAP server hostname
- **smtp_server** (str): SMTP server hostname
- **email** (str): Email address for authentication
- **password** (str): Password for authentication
- **imap_port** (int): IMAP server port (default: 993)
- **smtp_port** (int): SMTP server port (default: 587)
- **folder** (str): Email folder to monitor (default: "INBOX")
- **check_interval** (int): Interval between email checks in seconds (default: 60)
- **max_retries** (int): Maximum number of retry attempts for failed operations (default: 3)
- **timeout** (int): Connection timeout in seconds (default: 30)
- **tls** (bool): Whether to use TLS encryption (default: True)

Example Usage
-----------

.. code-block:: python

    from pymailai import EmailConfig

    config = EmailConfig(
        imap_server="imap.gmail.com",
        smtp_server="smtp.gmail.com",
        email="your-email@gmail.com",
        password="your-app-password",
        check_interval=30  # Check every 30 seconds
    )

    # Validate the configuration
    config.validate()
