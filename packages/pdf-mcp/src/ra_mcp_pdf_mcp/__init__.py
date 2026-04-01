from fastmcp import FastMCP


pdf_mcp = FastMCP(
    name="ra-pdf-mcp",
    instructions=(
        "PDF viewer for Riksarkivet's archival guides. "
        "search_guides and read_pdf_page work without display_pdf. "
        "pdf_go_to_page and pdf_set_search REQUIRE display_pdf first — call display_pdf before navigating or highlighting. "
        "Always cite page numbers and show the source in the viewer."
    ),
)

# Import tools module to trigger @mcp.tool registration
from ra_mcp_pdf_mcp import tools  # noqa: E402, F401


__all__ = ["pdf_mcp"]
