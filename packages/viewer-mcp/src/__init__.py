from fastmcp import FastMCP

mcp = FastMCP(name="Riksarkivet Document Viewer")

# Import tools module to trigger @mcp.tool registration
from src import tools  # noqa: E402, F401
