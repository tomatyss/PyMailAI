"""HTML to text conversion utilities with quote preservation."""

from typing import List, Tuple

from bs4 import BeautifulSoup


class HtmlConverter:
    """Handles conversion of HTML to text while preserving email quotes."""

    # Email client-specific quote selectors
    QUOTE_SELECTORS = [
        "blockquote",  # Standard HTML quotes
        "div.gmail_quote",  # Gmail
        'div[style*="margin-left: 1em"]',  # Common indented quotes
        'div[style*="border-left"]',  # Common quote styling
        ".yahoo_quoted",  # Yahoo
        ".outlook_quote",  # Outlook
        'div[data-marker="__QUOTED_TEXT__"]',  # Generic quote marker
    ]

    # HTML elements that may contain text content
    TEXT_ELEMENTS = ["p", "div", "span", "pre"]

    @classmethod
    def convert_html_to_text(cls, html_content: str) -> str:
        """Convert HTML content to text while preserving quotes.

        Args:
            html_content: The HTML content to convert

        Returns:
            Converted text with preserved quote formatting
        """
        soup = BeautifulSoup(html_content, "html.parser")
        main_text, quotes = cls._extract_content_and_quotes(soup)

        # Combine main content with quotes
        parts = []
        if main_text.strip():
            parts.append(main_text.strip())

        # Format and add quotes
        for quote in quotes:
            formatted_quote = "\n".join("> " + line for line in quote.split("\n"))
            parts.append(formatted_quote)

        return "\n\n".join(parts)

    @classmethod
    def _extract_content_and_quotes(cls, soup: BeautifulSoup) -> Tuple[str, List[str]]:
        """Extract main content and quoted text from HTML.

        Args:
            soup: BeautifulSoup object of the HTML content

        Returns:
            Tuple of (main_text, list_of_quotes)
        """
        quotes = []

        # Extract quotes first
        for quote in soup.select(", ".join(cls.QUOTE_SELECTORS)):
            quote_text = cls._extract_text_from_element(quote)
            if quote_text.strip():
                quotes.append(quote_text.strip())
            quote.decompose()  # Remove quote from soup

        # Extract remaining main content
        main_text = cls._extract_text_from_element(soup)

        return main_text, quotes

    @classmethod
    def _extract_text_from_element(cls, element: BeautifulSoup) -> str:
        """Extract text content from an HTML element, preserving basic structure.

        Args:
            element: BeautifulSoup element to extract text from

        Returns:
            Extracted text with preserved line breaks
        """
        text = ""
        for child in element.descendants:
            if child.name == "br":
                text += "\n"
            elif child.name in cls.TEXT_ELEMENTS:
                text += "\n"
                if child.get("class") and any(
                    "quote" in cls for cls in child.get("class")
                ):
                    text += "> "
            elif child.string:
                text += child.string.strip()
        return text
