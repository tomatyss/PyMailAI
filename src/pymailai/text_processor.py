"""Text processing utilities for email content."""

from typing import List


class TextProcessor:
    """Handles processing of plain text email content."""

    @classmethod
    def process_text_with_quotes(cls, content: str) -> str:
        """Process plain text content while preserving quote markers.

        Args:
            content: The plain text content to process

        Returns:
            Processed text with preserved quote formatting
        """
        lines = content.split("\n")
        parts: List[str] = []
        current_text: List[str] = []
        current_quote: List[str] = []

        for line in lines:
            if line.startswith(">"):
                if current_text:
                    parts.append("\n".join(current_text))
                    current_text = []
                current_quote.append(line)
            else:
                if current_quote:
                    parts.append("\n".join(current_quote))
                    current_quote = []
                current_text.append(line)

        # Add any remaining content
        if current_text:
            parts.append("\n".join(current_text))
        if current_quote:
            parts.append("\n".join(current_quote))

        return "\n".join(part for part in parts if part.strip())

    @classmethod
    def combine_text_parts(cls, parts: List[str]) -> str:
        """Combine multiple text parts while preserving structure.

        Args:
            parts: List of text parts to combine

        Returns:
            Combined text with proper spacing and structure
        """
        return "\n".join(part for part in parts if part.strip())
