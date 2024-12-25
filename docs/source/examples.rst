Examples
========

This section provides examples of how to use pymailai in different scenarios.

OpenAI Integration
----------------

Basic Example
~~~~~~~~~~~

This example shows how to create a simple email agent that processes incoming emails using OpenAI's GPT model
and sends back AI-generated responses.

.. literalinclude:: ../../examples/openai_completion.py
   :language: python
   :caption: OpenAI Email Agent Example
   :name: openai_example
   :linenos:

Advanced Example with Email Threading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example shows how to create an email agent that maintains proper email threading, including quoted
original messages and correct threading metadata.

.. literalinclude:: ../../examples/openai_completion_with_threading.py
   :language: python
   :caption: OpenAI Email Agent with Threading Example
   :name: openai_threading_example
   :linenos:

Key features of the threading example:

- Uses ``create_reply()`` to generate properly formatted responses
- Includes the original message as quoted text
- Sets correct threading metadata (References and In-Reply-To headers)
- Ensures emails appear properly threaded in email clients

Email Threading Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~

When creating email responses, it's important to maintain proper threading for a better user experience:

1. Include the original message as quoted text using ``create_reply()``
2. Preserve threading metadata for email client compatibility
3. Maintain conversation context with proper message quoting
4. Keep CC recipients in the loop

Example of creating a threaded reply:

.. code-block:: python

    # Create a properly threaded reply
    reply = message.create_reply(
        reply_text="Your response here",
        include_history=True  # Include quoted original message
    )
    reply.from_address = "your-email@example.com"

Running the Examples
~~~~~~~~~~~~~~~~

To run these examples:

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

Gmail Authentication
-----------------

pymailai supports two methods for Gmail authentication:

1. OAuth2 (for personal Gmail accounts)
2. Service Account (for Google Workspace accounts)

OAuth2 Authentication
~~~~~~~~~~~~~~~~~~

This example shows how to use Gmail OAuth2 authentication for personal Gmail accounts.

.. literalinclude:: ../../examples/gmail_credentials.py
   :language: python
   :caption: Gmail OAuth2 Example
   :name: gmail_oauth2_example
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

Service Account Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~

This example shows how to use Gmail service account authentication for Google Workspace accounts.

.. literalinclude:: ../../examples/gmail_service_account.py
   :language: python
   :caption: Gmail Service Account Example
   :name: gmail_service_account_example
   :linenos:

To use Gmail with service account authentication:

1. Set up Google Cloud Project:

   a. Go to the `Google Cloud Console <https://console.cloud.google.com/>`_
   b. Create a new project or select an existing one
   c. Enable the Gmail API
   d. Create a service account:
      - Click "Create Service Account"
      - Download the JSON key file
   e. Configure domain-wide delegation:
      - Go to Google Workspace Admin Console
      - Security -> API Controls -> Domain-wide Delegation
      - Add the service account's client ID
      - Add scope: ``https://www.googleapis.com/auth/gmail.modify``

2. Run the example:

   .. code-block:: bash

      # Update SERVICE_ACCOUNT_FILE and USER_EMAIL in the example
      python examples/gmail_service_account.py

The service account provides:
- Better security through domain-wide delegation
- No need for user interaction
- Support for multiple user impersonation
- Direct Gmail API access

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

- pymailai.client: Email client operations (SMTP/IMAP connections)
- pymailai.agent: AI agent activities (message processing)
- pymailai.gmail: Gmail-specific operations (OAuth2, service accounts)
- pymailai.gmail_client: Gmail API operations

Example log output at INFO level:

.. code-block:: text

   2024-03-20 10:15:30,123 - pymailai.gmail - INFO - Gmail service initialized for user@domain.com
   2024-03-20 10:15:30,456 - pymailai.gmail_client - INFO - Found 1 unread messages
   2024-03-20 10:15:30,789 - pymailai.agent - INFO - Processing message from: sender@example.com
   2024-03-20 10:15:31,012 - pymailai.gmail_client - INFO - Message sent successfully with ID: msg-123

Ollama Integration
----------------

This example shows how to create an email agent that processes incoming emails using Ollama's local LLM models
and sends back AI-generated responses.

.. literalinclude:: ../../examples/ollama_completion.py
   :language: python
   :caption: Ollama Email Agent Example
   :name: ollama_example
   :linenos:

To run this example:

1. Install the required dependencies:

   .. code-block:: bash

      pip install pymailai[ollama]

2. Install and start Ollama:

   Follow the instructions at https://ollama.ai to install Ollama for your platform.
   Then pull your desired model:

   .. code-block:: bash

      ollama pull llama3.2  # Latest Llama version

3. Set up the required environment variables:

   .. code-block:: bash

      export EMAIL_ADDRESS="your-email@example.com"
      export EMAIL_PASSWORD="your-email-password"
      export EMAIL_IMAP_SERVER="your-imap-server"
      export EMAIL_SMTP_SERVER="your-smtp-server"
      export EMAIL_IMAP_PORT="993"  # Default SSL/TLS port for IMAP
      export EMAIL_SMTP_PORT="465"  # Default SSL/TLS port for SMTP

4. Run the example:

   .. code-block:: bash

      python examples/ollama_completion.py

The agent will monitor the specified email account and:

1. Process any new incoming emails
2. Send the email content to the local Ollama instance
3. Send back the AI-generated response to the original sender

Simple AI Agent
--------------

For a simpler example without external AI providers, check out the :file:`examples/simple_ai_agent.py` file
in the repository. This example shows the basic structure of creating a custom message handler.
