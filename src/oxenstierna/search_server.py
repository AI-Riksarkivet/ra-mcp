from typing import Annotated
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from oxenstierna.ra_api.search_client import RiksarkivetSearchClient

search_mcp = FastMCP(
    name="htr_server",
    instructions="""
    🔍 Swedish National Archives Search Server
    
    Search the Riksarkivet database for historical documents and records.
    
    USAGE:
    - search_records("keywords") → Find relevant archives
    - Results include PIDs for accessing collections
    - Use PIDs with IIIF tools to explore and download content
    
    SEARCH EXAMPLES:
    - search_records("coffee") → Documents about coffee
    - search_records("kyrkoböcker") → Church records (Swedish term)
    - search_records("trade", only_digitized=False) → Include non-digitized
    
    WORKFLOW:
    1. Search for keywords → Get PIDs
    2. Use PIDs with collection/manifest tools → Access documents
    """,
)

search_client = RiksarkivetSearchClient()


@search_mcp.tool(
    tags={"search"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Search Records",
    },
)
async def search_records(
    query: Annotated[
        str,
        Field(
            description="Search terms (e.g., 'coffee', 'medical records', 'church documents')",
            min_length=1,
            max_length=200,
        ),
    ],
    only_digitized: Annotated[
        bool,
        Field(description="Only return digitized materials (default: True)"),
    ] = True,
    offset: Annotated[
        int,
        Field(description="Pagination offset (default: 0)", ge=0),
    ] = 0,
) -> str:
    """
    Search the Riksarkivet records database by keywords.

    Returns search results with PIDs that you can use with other tools.
    This is typically the first step in discovering archival content.
    """
    try:
        results = await search_client.search_records(query, only_digitized, offset)

        if not results.results:
            return f"No results found for '{query}'. Try different keywords or set only_digitized=False."

        info_lines = [
            f"Search Results for '{query}':",
            f"Total hits: {results.total_hits} (showing {results.hits} from offset {results.offset})",
            "",
        ]

        for i, result in enumerate(results.results, 1):
            info_lines.append(f"{i}. {result.caption}")
            info_lines.append(f"   PID: {result.id}")
            info_lines.append(f"   Type: {result.object_type} - {result.type}")
            if result.reference_code:
                info_lines.append(f"   Reference: {result.reference_code}")
            info_lines.append("")

        info_lines.append("Next steps:")
        info_lines.append("- Use get_collection_info(pid) to explore a collection")
        info_lines.append(
            "- Use get_all_manifests_from_pid(pid) to see all image batches"
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")
