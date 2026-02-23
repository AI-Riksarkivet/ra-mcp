from fastmcp import FastMCP


viewer_mcp = FastMCP(name="ra-viewer-mcp")

# Import tools module to trigger @mcp.tool registration
from ra_mcp_viewer_mcp import tools  # noqa: E402, F401


__all__ = ["viewer_mcp"]
