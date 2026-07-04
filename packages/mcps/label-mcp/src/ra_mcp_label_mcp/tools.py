"""
Riksarkivet Label Studio MCP Server.

This module sets up the FastMCP server and registers label tools
for importing pages to Label Studio for human annotation.
"""

from fastmcp import FastMCP

from .label_tool import register_label_tool


label_mcp = FastMCP(
    name="ra-label-mcp",
    instructions="""
    Riksarkivet Label Studio MCP Server

    Imports document pages to a Label Studio project for human annotation and feedback.

    TOOLS:
    - import_to_label_studio: Import pages to Label Studio for annotation
      Two modes:
      - With alto_urls: pre-annotated tasks with VectorLabels polygons and transcriptions
      - Without alto_urls: blank image-only tasks for annotation from scratch
      Set dry_run=true to preview converted tasks without importing.
      Label Studio URL, token, and project ID can be set via env vars (LS_URL, LS_TOKEN, LS_PROJECT_ID).

    WORKFLOW:
    1. Get image URLs (and optionally ALTO XML URLs) from browse_document results
    2. Call import_to_label_studio with the URL lists to import
    """,
)


# Register label tool
register_label_tool(label_mcp)
