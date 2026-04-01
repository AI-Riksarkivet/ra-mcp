from fastmcp import FastMCP


pdf_mcp = FastMCP(
    name="ra-pdf-mcp",
    instructions=(
        "PDF viewer for Riksarkivet's archival guides. "
        "Use search_guides to search ALL guides at once (no display_pdf needed). "
        "Use display_pdf to open a guide in the viewer, then read_pdf_page to read pages, "
        "pdf_go_to_page/pdf_set_search to navigate/highlight. "
        "Always cite page numbers and navigate the viewer to show the source."
    ),
)

# Import tools module to trigger @mcp.tool registration
from ra_mcp_pdf_mcp import tools  # noqa: E402, F401


__all__ = ["pdf_mcp"]
