"""
Generic formatting utilities.

Provides error message formatting that can be used across all packages.
"""

from typing import List, Optional


def format_error_message(error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
    """
    Format an error message with optional suggestions.

    Args:
        error_message: The error message to format
        error_suggestions: Optional list of suggestions to help resolve the error

    Returns:
        Formatted error message string with emoji and markdown
    """
    formatted_lines = []
    formatted_lines.append(f"⚠️ **Error**: {error_message}")

    if error_suggestions:
        formatted_lines.append("\n**Suggestions**:")
        for suggestion_text in error_suggestions:
            formatted_lines.append(f"- {suggestion_text}")

    return "\n".join(formatted_lines)


__all__ = ["format_error_message"]
