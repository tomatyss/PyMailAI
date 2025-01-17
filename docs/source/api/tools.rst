Tools
=====

The ``tools`` package provides functionality for integrating email sending capabilities with AI models like Anthropic's Claude and OpenAI's GPT. The package is organized into the following modules:

* ``core``: Contains core email functionality (execute_query_emails, execute_send_email)
* ``schemas``: Contains schema definitions for different AI models (Anthropic, OpenAI, Ollama)

All functions are conveniently exposed at the package level for easy importing.

Tool Schemas
-----------

.. py:function:: get_email_tool_schema_anthropic()

   Get the email tool schema formatted for Anthropic Claude models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage with Gmail:

   .. code-block:: python

      from pymailai.gmail import create_gmail_client
      from pymailai.tools import get_email_tool_schema_anthropic, execute_send_email

      # 1. Initialize Gmail client
      gmail = await create_gmail_client()

      # 2. Set up tool schema
      tools = get_email_tool_schema_anthropic()

      # 3. Make API call with tool
      response = await client.messages.create(
          model="claude-3-opus-20240229",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

      # 4. Execute tool calls from response
      for tool_call in response.content[0].tool_calls or []:
          if tool_call.name == "send_email":
              result = await execute_send_email(
                  gmail,
                  to=tool_call.parameters["to"],
                  subject=tool_call.parameters["subject"],
                  body=tool_call.parameters["body"],
                  cc=tool_call.parameters.get("cc"),
              )
              print(f"Email send result: {result}")

   Example usage with IMAP/SMTP:

   .. code-block:: python

      from pymailai.config import EmailConfig
      from pymailai.client import EmailClient
      from pymailai.tools import get_email_tool_schema_anthropic, execute_send_email

      # 1. Initialize IMAP/SMTP client
      config = EmailConfig(
          email="your-email@example.com",
          password="your-password",
          imap_server="imap.example.com",
          smtp_server="smtp.example.com",
          imap_port=993,  # Default SSL/TLS port
          smtp_port=465,  # Default SSL/TLS port
      )
      email_client = EmailClient(config)

      # 2. Set up tool schema
      tools = get_email_tool_schema_anthropic()

      # 3. Make API call with tool
      response = await client.messages.create(
          model="claude-3-opus-20240229",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

      # 4. Execute tool calls from response
      for tool_call in response.content[0].tool_calls or []:
          if tool_call.name == "send_email":
              result = await execute_send_email(
                  email_client,
                  to=tool_call.parameters["to"],
                  subject=tool_call.parameters["subject"],
                  body=tool_call.parameters["body"],
                  cc=tool_call.parameters.get("cc"),
              )
              print(f"Email send result: {result}")

.. py:function:: get_email_tool_schema_openai()

   Get the email tool schema formatted for OpenAI GPT models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage with Gmail:

   .. code-block:: python

      from pymailai.gmail import create_gmail_client
      from pymailai.tools import get_email_tool_schema_openai, execute_send_email

      # 1. Initialize Gmail client
      gmail = await create_gmail_client()

      # 2. Set up tool schema
      tools = get_email_tool_schema_openai()

      # 3. Make API call with tool
      completion = await client.chat.completions.create(
          model="gpt-4",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

      # 4. Execute tool calls from response
      for tool_call in completion.choices[0].message.tool_calls or []:
          if tool_call.function.name == "send_email":
              result = await execute_send_email(
                  gmail,
                  to=tool_call.function.arguments["to"],
                  subject=tool_call.function.arguments["subject"],
                  body=tool_call.function.arguments["body"],
                  cc=tool_call.function.arguments.get("cc"),
              )
              print(f"Email send result: {result}")

   Example usage with IMAP/SMTP:

   .. code-block:: python

      from pymailai.config import EmailConfig
      from pymailai.client import EmailClient
      from pymailai.tools import get_email_tool_schema_openai, execute_send_email

      # 1. Initialize IMAP/SMTP client
      config = EmailConfig(
          email="your-email@example.com",
          password="your-password",
          imap_server="imap.example.com",
          smtp_server="smtp.example.com",
      )
      email_client = EmailClient(config)

      # Rest of the code is the same as Gmail example...

.. py:function:: get_email_tool_schema_ollama()

   Get the email tool schema formatted for Ollama models.

   :return: A dictionary containing the tool schema
   :rtype: dict

   Example usage with Gmail:

   .. code-block:: python

      from pymailai.gmail import create_gmail_client
      from pymailai.tools import get_email_tool_schema_ollama, execute_send_email

      # 1. Initialize Gmail client
      gmail = await create_gmail_client()

      # 2. Set up tool schema
      tools = get_email_tool_schema_ollama()

      # 3. Make API call with tool
      response = ollama.chat(
          model="llama3.1",
          tools=tools,
          messages=[{"role": "user", "content": "Send an email..."}]
      )

      # 4. Execute tool calls from response
      for tool_call in response["message"].get("tool_calls", []):
          if tool_call["function"]["name"] == "send_email":
              result = await execute_send_email(
                  gmail,
                  to=tool_call["function"]["arguments"]["to"],
                  subject=tool_call["function"]["arguments"]["subject"],
                  body=tool_call["function"]["arguments"]["body"],
                  cc=tool_call["function"]["arguments"].get("cc"),
              )
              print(f"Email send result: {result}")

   Example usage with IMAP/SMTP:

   .. code-block:: python

      from pymailai.config import EmailConfig
      from pymailai.client import EmailClient
      from pymailai.tools import get_email_tool_schema_ollama, execute_send_email

      # 1. Initialize IMAP/SMTP client
      config = EmailConfig(
          email="your-email@example.com",
          password="your-password",
          imap_server="imap.example.com",
          smtp_server="smtp.example.com",
      )
      email_client = EmailClient(config)

      # Rest of the code is the same as Gmail example...

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

   Example usage with Gmail:

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

   Example usage with IMAP/SMTP:

   .. code-block:: python

      from pymailai.tools import execute_send_email
      from pymailai.config import EmailConfig
      from pymailai.client import EmailClient

      # Initialize IMAP/SMTP client
      config = EmailConfig(
          email="your-email@example.com",
          password="your-password",
          imap_server="imap.example.com",
          smtp_server="smtp.example.com",
      )
      email_client = EmailClient(config)

      # Send email
      result = await execute_send_email(
          email_client,
          to=["recipient@example.com"],
          subject="Test Email",
          body="Hello from PyMailAI!",
          cc=["cc@example.com"]
      )
      print(f"Email send result: {result}")

Using the Email Tool
----------------

The process of using the email tool involves four main steps:

1. Initialize the Email Client:
   You can use either Gmail API or standard IMAP/SMTP:

   Gmail API:
   .. code-block:: python

      from pymailai.gmail import create_gmail_client
      gmail = await create_gmail_client()

   IMAP/SMTP:
   .. code-block:: python

      from pymailai.config import EmailConfig
      from pymailai.client import EmailClient

      config = EmailConfig(
          email="your-email@example.com",
          password="your-password",
          imap_server="imap.example.com",
          smtp_server="smtp.example.com",
      )
      email_client = EmailClient(config)

2. Set up the Tool Schema:
   - Choose the appropriate schema for your AI model
   - Add it to the tools list in your API call

3. Make the API Call:
   - Include the tool schema in your model request
   - The model will generate tool calls in its response

4. Execute the Tool Calls:
   - Process the tool calls from the model's response
   - Use execute_send_email() to actually send the emails
   - Handle the results appropriately

Tool Schema Format
----------------

The email tool schema includes the following fields:

* ``to`` (required): List of recipient email addresses
* ``subject`` (required): Email subject line
* ``body`` (required): Email body content (supports markdown formatting)
* ``cc`` (optional): List of CC recipients

For both Anthropic and OpenAI models, the schema follows their respective formats while maintaining consistent functionality.
