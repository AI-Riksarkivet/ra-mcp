from fastmcp import FastMCP


pdf_mcp = FastMCP(name="ra-pdf-mcp")

# Import tools module to trigger @mcp.tool registration
from ra_mcp_pdf_mcp import tools  # noqa: E402, F401


__all__ = ["pdf_mcp"]
