"""Module for converting markdown content to HTML."""
from typing import List, Optional

import markdown  # type: ignore
from markdown.core import Markdown  # type: ignore


class MarkdownConverter:
    """Converts markdown content to HTML."""

    def __init__(self, extensions: Optional[List[str]] = None):
        """Initialize the markdown converter.

        Args:
            extensions: List of markdown extensions to use. If None, uses default extensions.
        """
        self.extensions = extensions or [
            "tables",
            "fenced_code",
            "codehilite",
            "nl2br",
        ]
        self.md: Markdown = markdown.Markdown(extensions=self.extensions)

    def convert(self, content: str) -> str:
        """Convert markdown content to HTML.

        Args:
            content: The markdown content to convert.

        Returns:
            The HTML representation of the markdown content.
        """
        result = self.md.convert(content)
        assert isinstance(result, str)  # Runtime check for mypy
        return result

    def reset(self) -> None:
        """Reset the markdown converter instance.

        This is useful when converting multiple documents, as the markdown
        converter maintains some internal state.
        """
        self.md.reset()
