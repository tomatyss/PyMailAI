Email Agent
==========

The EmailAgent class is the main component of pymailai that handles email processing and AI-powered responses.

.. autoclass:: pymailai.agent.EmailAgent
   :members:
   :special-members: __aenter__, __aexit__
   :show-inheritance:

Type Definitions
--------------

.. py:data:: pymailai.agent.MessageHandler
   :type: Callable[[EmailData], Coroutine[Any, Any, Optional[EmailData]]]

   Type alias for message handler functions that process incoming emails.
   
   The handler should be an async function that takes an :class:`EmailData` object
   and returns an optional response :class:`EmailData`.
