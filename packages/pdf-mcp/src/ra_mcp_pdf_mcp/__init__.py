from fastmcp import FastMCP


pdf_mcp = FastMCP(
    name="ra-pdf-mcp",
    instructions=(
        "PDF viewer for Riksarkivet's archival guides. "
        "WORKFLOW: display_pdf (opens viewer) → search_pdf (find text) → read_pdf_page (read pages) → pdf_go_to_page/pdf_set_search (navigate/highlight). "
        "Always call display_pdf FIRST — all other tools require it."
    ),
)

# Import tools module to trigger @mcp.tool registration
from ra_mcp_pdf_mcp import tools  # noqa: E402, F401


__all__ = ["pdf_mcp"]
