Examples
========

This section provides examples of how to use pymailai in different scenarios.

OpenAI Integration
----------------

This example shows how to create an email agent that processes incoming emails using OpenAI's GPT model
and sends back AI-generated responses.

.. literalinclude:: ../../examples/openai_completion.py
   :language: python
   :caption: OpenAI Email Agent Example
   :name: openai_example
   :linenos:

To run this example:

1. Install the required dependencies:

   .. code-block:: bash

      pip install pymailai[openai]

2. Set up the required environment variables:

   .. code-block:: bash

      export OPENAI_API_KEY="your-openai-api-key"
      export EMAIL_ADDRESS="your-email@example.com"
      export EMAIL_PASSWORD="your-email-password"
      # Optional: Configure custom email servers
      export EMAIL_IMAP_SERVER="imap.gmail.com"
      export EMAIL_SMTP_SERVER="smtp.gmail.com"

3. Run the example:

   .. code-block:: bash

      python examples/openai_completion.py

The agent will monitor the specified email account and:

1. Process any new incoming emails
2. Send the email content to OpenAI's API
3. Send back the AI-generated response to the original sender

Anthropic Integration
-------------------

This example shows how to create an email agent that processes incoming emails using Anthropic's Claude model
and sends back AI-generated responses.

.. literalinclude:: ../../examples/anthropic_completion.py
   :language: python
   :caption: Anthropic Email Agent Example
   :name: anthropic_example
   :linenos:

To run this example:

1. Install the required dependencies:

   .. code-block:: bash

      pip install pymailai[anthropic]

2. Set up the required environment variables:

   .. code-block:: bash

      export ANTHROPIC_API_KEY="your-anthropic-api-key"
      export EMAIL_ADDRESS="your-email@example.com"
      export EMAIL_PASSWORD="your-email-password"
      # Optional: Configure custom email servers
      export EMAIL_IMAP_SERVER="imap.gmail.com"
      export EMAIL_SMTP_SERVER="smtp.gmail.com"

3. Run the example:

   .. code-block:: bash

      python examples/anthropic_completion.py

The agent will monitor the specified email account and:

1. Process any new incoming emails
2. Send the email content to Anthropic's API
3. Send back the AI-generated response to the original sender

Gmail OAuth2 Integration
----------------------

This example shows how to use Gmail OAuth2 authentication instead of password-based authentication.
This is the recommended approach for Gmail accounts as it provides better security and avoids
issues with 2-factor authentication and app-specific passwords.

.. literalinclude:: ../../examples/gmail_credentials.py
   :language: python
   :caption: Gmail Credentials Example
   :name: gmail_example
   :linenos:

To use Gmail with OAuth2 credentials:

1. Set up a Google Cloud Project and enable the Gmail API:

   a. Go to the `Google Cloud Console <https://console.cloud.google.com/>`_
   b. Create a new project or select an existing one
   c. Enable the Gmail API
   d. Create OAuth2 credentials:
      - Click "Create Credentials" and select "OAuth client ID"
      - Choose "Desktop application" as the application type
      - Download the credentials JSON file
   e. Configure the OAuth consent screen:
      - Add your email address as a test user
      - Set the necessary scopes (gmail.modify, gmail.compose, gmail.send)

2. Get a refresh token using the provided helper script:

   .. code-block:: bash

      # First time setup - this will create the credentials file
      export GMAIL_CLIENT_ID="your-client-id"
      export GMAIL_CLIENT_SECRET="your-client-secret"
      export GMAIL_REFRESH_TOKEN="your-refresh-token"
      export GMAIL_ADDRESS="your-gmail@gmail.com"

      # Run the example to save credentials
      python examples/gmail_credentials.py

The credentials will be saved to ``~/.config/pymailai/gmail_creds.json``. Future runs will load
the credentials from this file automatically.

Logging Configuration
------------------

pymailai includes comprehensive logging for debugging and monitoring. You can configure the logging
level and output format:

.. code-block:: python

   import logging

   # Configure logging for the entire package
   logging.basicConfig(
       level=logging.INFO,  # or logging.DEBUG for more detailed output
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )

   # Or configure logging for specific components
   logger = logging.getLogger('pymailai.client')
   logger.setLevel(logging.DEBUG)

The following components have dedicated loggers:

- pymailai.client: Email client operations (SMTP/IMAP connections, message operations)
- pymailai.agent: AI agent activities (message processing, AI interactions)
- pymailai.gmail: Gmail-specific operations (OAuth2, credential management)

Example log output at DEBUG level:

.. code-block:: text

   2023-07-20 10:15:30,123 - pymailai.client - DEBUG - Connecting to SMTP server smtp.gmail.com:587
   2023-07-20 10:15:30,456 - pymailai.client - INFO - Successfully connected to SMTP server
   2023-07-20 10:15:30,789 - pymailai.gmail - DEBUG - Refreshing OAuth2 token
   2023-07-20 10:15:31,012 - pymailai.client - INFO - Successfully authenticated with OAuth2

Simple AI Agent
--------------

For a simpler example without external AI providers, check out the :file:`examples/simple_ai_agent.py` file
in the repository. This example shows the basic structure of creating a custom message handler.
