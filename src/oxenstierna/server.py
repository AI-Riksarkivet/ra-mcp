from fastmcp import FastMCP
from oxenstierna.htr_server import htr_server
from oxenstierna.search_server import search_mcp
from oxenstierna.iiif_server import iiif_mcp


mcp = FastMCP(
    name="Main Server",
    instructions="""
    🏛️ Oxenstierna Server
    This server provides access to various tools for processing historical documents, including:
    
    - Handwritten Text Recognition (HTR)
    - Search functionality for Swedish National Archives records
    - IIIF image and data access for historical documents
    
    Use the available tools to interact with historical documents and data.
    """,
)

mcp.mount("htr", htr_server)
mcp.mount("search", search_mcp)
mcp.mount("iiif", iiif_mcp)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        print("Starting FastMCP HTTP server on http://localhost:8000")
        mcp.run(transport="sse", host="localhost", port=8000)
    else:
        print("Starting FastMCP stdio server")
        mcp.run(transport="stdio")
