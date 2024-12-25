"""PyMailAI - Email interface for AI agents."""

from pymailai.agent import EmailAgent
from pymailai.config import EmailConfig
from pymailai.gmail import GmailCredentials
from pymailai.markdown_converter import MarkdownConverter

__version__ = "0.1.0"
__all__ = ["EmailAgent", "EmailConfig", "GmailCredentials", "MarkdownConverter"]
