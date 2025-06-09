from fastmcp import FastMCP
from oxenstierna.htr_server import htr_server
from oxenstierna.search_server import search_mcp
from oxenstierna.iiif_server import iiif_mcp

mcp_main = FastMCP(
    name="Main Server",
    instructions="""
    🏛️ Oxenstierna Server
    This server provides access to various tools for processing historical documents, including:
    
    - Handwritten Text Recognition (HTR)
    - Search functionality for Swedish National Archives records
    - Image processing and analysis tools
    
    Use the available tools to interact with historical documents and data.
    """,
)

mcp_main.mount("htr", htr_server)
mcp_main.mount("search", search_mcp)
mcp_main.mount("iiif", iiif_mcp)

if __name__ == "__main__":
    mcp_main.run(transport="stdio")
