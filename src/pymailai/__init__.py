"""PyMailAI - Email interface for AI agents."""

from pymailai.agent import EmailAgent
from pymailai.config import EmailConfig

__version__ = "0.1.0"
__all__ = ["EmailAgent", "EmailConfig", "GmailCredentials"]

from pymailai.gmail import GmailCredentials
