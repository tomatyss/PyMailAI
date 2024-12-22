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

Simple AI Agent
--------------

For a simpler example without external AI providers, check out the :file:`examples/simple_ai_agent.py` file
in the repository. This example shows the basic structure of creating a custom message handler.
