"""
Riksarkivet Historical Guide MCP Server.

Provides MCP resources for accessing historical documentation about Swedish archives.
"""

import os
from typing import List, Optional

from fastmcp import FastMCP


def format_error_message(error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
    """Format an error message with optional suggestions."""
    formatted_lines = [f"⚠️ **Error**: {error_message}"]
    if error_suggestions:
        formatted_lines.append("\n**Suggestions**:")
        for suggestion_text in error_suggestions:
            formatted_lines.append(f"- {suggestion_text}")
    return "\n".join(formatted_lines)


guide_mcp = FastMCP(
    name="ra-guide-mcp",
    instructions="""
    📚 Riksarkivet Historical Guide MCP Server

    This server provides access to historical documentation about Swedish archives,
    including guides about court records, prisons, and other archival materials.

    AVAILABLE RESOURCES:

    1. 📑 riksarkivet://contents/table_of_contents
       - Returns the complete guide index (Innehållsförteckning)
       - Lists all available historical guide sections

    2. 📄 riksarkivet://guide/{filename}
       - Access detailed historical documentation by filename
       - Examples: '01_Domstolar.md', '02_Fangelse.md'
       - Use table_of_contents to see available sections

    TYPICAL WORKFLOW:
    1. Access table_of_contents to see all available guide sections
    2. Load specific sections using guide/{filename}
    3. Use guide content to understand historical context for search results

    All resources return markdown-formatted historical documentation.
    """,
)


@guide_mcp.resource("riksarkivet://contents/table_of_contents")
def get_table_of_contents() -> str:
    """
    Get the table of contents (Innehållsförteckning) for the Riksarkivet historical guide.
    """
    try:
        content = _load_markdown_file("00_Innehallsforteckning.md")
        return content

    except FileNotFoundError:
        return format_error_message(
            "Table of contents file not found",
            error_suggestions=[
                "Check if the markdown/00_Innehallsforteckning.md file exists",
                "Verify the file path is correct",
            ],
        )
    except Exception as e:
        return format_error_message(
            f"Failed to load table of contents: {str(e)}",
            error_suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
            ],
        )


@guide_mcp.resource("riksarkivet://guide/{filename}")
def get_guide_content(filename: str) -> str:
    """
    Load content from specific sections of the Riksarkivet historical guide.

    Args:
        filename: Markdown filename to load (e.g., '01_Domstolar.md', '02_Fangelse.md')

    Returns:
        The content of the requested guide section
    """
    try:
        if not _validate_markdown_filename(filename):
            return _generate_invalid_filename_message()

        if not _check_file_exists(filename):
            return _generate_file_not_found_message(filename)

        content = _load_markdown_file(filename)
        return content

    except Exception as e:
        return format_error_message(
            f"Failed to load guide content '{filename}': {str(e)}",
            error_suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
                "Ensure the filename is valid",
            ],
        )


def _validate_markdown_filename(filename):
    """Validate that the filename has .md extension."""
    return filename.endswith(".md")


def _generate_invalid_filename_message():
    """Generate error message for invalid filename format."""
    return format_error_message(
        "Invalid filename format",
        error_suggestions=["Filename must end with .md extension"],
    )


def _check_file_exists(filename):
    """Check if the markdown file exists."""
    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)
    markdown_path = os.path.join(current_dir, "..", "..", "..", "..", "resources", filename)
    if not os.path.exists(markdown_path):
        # Try alternative paths for different package layouts
        alt_paths = [
            os.path.join(current_dir, "..", "..", "..", "..", "..", "resources", filename),
            os.path.join(current_dir, "..", "..", "..", "..", "..", "markdown", filename),
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                return True
    return os.path.exists(markdown_path)


def _generate_file_not_found_message(filename):
    """Generate error message when file is not found."""
    return format_error_message(
        f"Guide section '{filename}' not found",
        error_suggestions=[
            "Check the filename spelling",
            "Use get_table_of_contents resource to see available sections",
            "Ensure the filename includes .md extension",
        ],
    )


def _load_markdown_file(filename):
    """Load content from a markdown file."""
    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)

    # Try multiple possible paths
    possible_paths = [
        os.path.join(current_dir, "..", "..", "..", "..", "resources", filename),
        os.path.join(current_dir, "..", "..", "..", "..", "..", "resources", filename),
        os.path.join(current_dir, "..", "..", "..", "..", "..", "markdown", filename),
    ]

    for markdown_path in possible_paths:
        if os.path.exists(markdown_path):
            with open(markdown_path, "r", encoding="utf-8") as f:
                return f.read()

    # Default path for error message
    raise FileNotFoundError(f"Could not find {filename} in any expected location")
