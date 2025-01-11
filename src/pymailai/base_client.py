"""Base email client interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from pymailai.message import EmailData


class BaseEmailClient(ABC):
    """Abstract base class for email clients."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the email service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the email service."""
        pass

    @abstractmethod
    async def fetch_new_messages(self) -> AsyncGenerator[EmailData, None]:
        """Fetch new messages from the email service.

        Yields:
            EmailData objects for new messages.
        """
        yield  # type: ignore

    @abstractmethod
    async def send_message(self, message: EmailData) -> None:
        """Send an email message."""
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read."""
        pass

    @abstractmethod
    async def query_messages(
        self, query_params: dict
    ) -> AsyncGenerator[EmailData, None]:
        """Query messages based on specified parameters.

        Args:
            query_params: Dictionary containing query parameters:
                - after_date: Optional[str] - Messages after this date (YYYY-MM-DD)
                - before_date: Optional[str] - Messages before this date (YYYY-MM-DD)
                - subject: Optional[str] - Subject line contains this text
                - from_address: Optional[str] - Sender email address
                - to_address: Optional[str] - Recipient email address
                - label: Optional[str] - Message label/folder
                - unread_only: Optional[bool] - Only unread messages if True
                - include_body: Optional[bool] - Include message body in results

        Yields:
            EmailData objects for matching messages
        """
        yield  # type: ignore

    async def __aenter__(self) -> "BaseEmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
