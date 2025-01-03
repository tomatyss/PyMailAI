Tools
=====

The ``tools`` module provides functionality for integrating email sending capabilities with AI models like Anthropic's Claude and OpenAI's GPT.

Tool Schemas
-----------

.. py:function:: get_email_tool_schema_anthropic()

   Get the email tool schema formatted for Anthropic Claude models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage:

   .. code-block:: python

      from pymailai.tools import get_email_tool_schema_anthropic

      tools = [get_email_tool_schema_anthropic()]
      response = await client.messages.create(
          model="claude-3-opus-20240229",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

.. py:function:: get_email_tool_schema_openai()

   Get the email tool schema formatted for OpenAI GPT models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage:

   .. code-block:: python

      from pymailai.tools import get_email_tool_schema_openai

      tools = [get_email_tool_schema_openai()]
      completion = await client.chat.completions.create(
          model="gpt-4",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

.. py:function:: get_email_tool_schema_ollama()

   Get the email tool schema formatted for Ollama models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage:

   .. code-block:: python

      from pymailai.tools import get_email_tool_schema_ollama

      response = ollama.chat(
          model="llama3.1",
          tools=[get_email_tool_schema_ollama()],
          messages=[{"role": "user", "content": "Send an email..."}]
      )

Tool Execution
-------------

.. py:function:: execute_send_email(client, to, subject, body, cc=None)

   Execute the send_email tool using the provided email client.

   :param client: Email client instance to use for sending
   :type client: BaseEmailClient
   :param to: List of recipient email addresses
   :type to: List[str]
   :param subject: Email subject line
   :type subject: str
   :param body: Email body content (supports markdown formatting)
   :type body: str
   :param cc: Optional list of CC recipients
   :type cc: Optional[List[str]]
   :return: Dictionary containing success status and any error message
   :rtype: Dict[str, Union[bool, str]]

   Example usage:

   .. code-block:: python

      from pymailai.tools import execute_send_email
      from pymailai.gmail import create_gmail_client

      # Initialize Gmail client
      gmail = await create_gmail_client()

      # Send email
      result = await execute_send_email(
          gmail,
          to=["recipient@example.com"],
          subject="Test Email",
          body="Hello from PyMailAI!",
          cc=["cc@example.com"]
      )
      print(f"Email send result: {result}")

Tool Schema Format
----------------

The email tool schema includes the following fields:

* ``to`` (required): List of recipient email addresses
* ``subject`` (required): Email subject line
* ``body`` (required): Email body content (supports markdown formatting)
* ``cc`` (optional): List of CC recipients

For both Anthropic and OpenAI models, the schema follows their respective formats while maintaining consistent functionality.
