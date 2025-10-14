"""
Base display service with shared functionality for both browse and search.
"""

from typing import Optional, List
from ..formatters import PlainTextFormatter


class BaseDisplayService:
    """Base display service with shared formatting functionality."""

    def __init__(self, formatter=None, show_border=None):
        """
        Initialize the base display service.

        Args:
            formatter: Formatter instance to use (PlainTextFormatter or RichConsoleFormatter)
                      If None, defaults to PlainTextFormatter
            show_border: Whether to show borders/separators in output. If None, determines based on formatter type
        """
        self.formatter = formatter or PlainTextFormatter()
        # Determine border visibility - PlainTextFormatter (MCP mode) typically doesn't show borders
        self.show_border = show_border if show_border is not None else not isinstance(self.formatter, PlainTextFormatter)

    def format_error_message(self, error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
        """Format error messages as string."""
        formatted_lines = [f"❌ Error: {error_message}"]

        if error_suggestions:
            formatted_lines.append("")
            formatted_lines.append("💡 Suggestions:")
            for suggestion_text in error_suggestions:
                formatted_lines.append(f"  • {suggestion_text}")

        return "\n".join(formatted_lines)

    def format_logging_status(self, enabled: bool) -> Optional[str]:
        """Format logging status message.

        Args:
            enabled: Whether logging is enabled

        Returns:
            Status message or None if logging disabled
        """
        if enabled:
            return "[dim]API logging enabled - check ra_mcp_api.log[/dim]"
        return None
