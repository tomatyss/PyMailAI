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

    async def __aenter__(self) -> "BaseEmailClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
