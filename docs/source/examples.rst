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

Gmail Credentials
---------------

This example shows how to use Gmail credentials from a file instead of environment variables.
This is particularly useful for applications that need to manage multiple Gmail accounts or
want to securely store OAuth2 credentials.

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
   d. Create OAuth2 credentials (Desktop application type)
   e. Download the credentials

2. Get a refresh token:

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

Simple AI Agent
--------------

For a simpler example without external AI providers, check out the :file:`examples/simple_ai_agent.py` file
in the repository. This example shows the basic structure of creating a custom message handler.
