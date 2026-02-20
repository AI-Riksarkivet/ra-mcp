"""
Riksarkivet Historical Guide MCP Server.

Provides MCP resources for accessing historical documentation about Swedish archives.
"""

from pathlib import Path

from fastmcp import FastMCP

from ra_mcp_common.utils.formatting import format_error_message


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
            f"Failed to load table of contents: {e!s}",
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
            f"Failed to load guide content '{filename}': {e!s}",
            error_suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
                "Ensure the filename is valid",
            ],
        )


def _validate_markdown_filename(filename) -> bool:
    """Validate that the filename has .md extension."""
    return filename.endswith(".md")


def _generate_invalid_filename_message() -> str:
    """Generate error message for invalid filename format."""
    return format_error_message(
        "Invalid filename format",
        error_suggestions=["Filename must end with .md extension"],
    )


def _find_resources_dir() -> Path:
    """Locate the resources directory.

    Checks two locations:
    1. Inside the guide-mcp package (development / editable install)
    2. Working directory ``resources/`` (Docker production with --no-editable)
    """
    # Development: resources/ lives next to src/ in the guide-mcp package
    # tools.py -> ra_mcp_guide_mcp/ -> src/ -> guide-mcp/ -> resources/
    pkg_resources = Path(__file__).resolve().parent.parent.parent / "resources"
    if pkg_resources.is_dir():
        return pkg_resources

    # Production (Docker): resources/ is copied to the working directory
    cwd_resources = Path("resources")
    if cwd_resources.is_dir():
        return cwd_resources.resolve()

    return pkg_resources  # fall back so error messages reference a sensible path


_RESOURCES_DIR = _find_resources_dir()


def _check_file_exists(filename) -> bool:
    """Check if the markdown file exists."""
    safe_name = Path(filename).name
    return (_RESOURCES_DIR / safe_name).exists()


def _generate_file_not_found_message(filename) -> str:
    """Generate error message when file is not found."""
    return format_error_message(
        f"Guide section '{filename}' not found",
        error_suggestions=[
            "Check the filename spelling",
            "Use get_table_of_contents resource to see available sections",
            "Ensure the filename includes .md extension",
        ],
    )


def _load_markdown_file(filename) -> str:
    """Load content from a markdown file."""
    safe_name = Path(filename).name
    path = _RESOURCES_DIR / safe_name

    if not path.exists():
        raise FileNotFoundError(f"Could not find {safe_name} in {_RESOURCES_DIR}")

    return path.read_text(encoding="utf-8")
