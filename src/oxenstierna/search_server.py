from typing import Annotated, Optional
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from oxenstierna.ra_api.search_client import RiksarkivetSearchClient
from oxenstierna.ra_api.models.search_model import ObjectType, SortOption, Provenance

search_mcp = FastMCP(
    name="htr_server",
    instructions="""
    🔍 Swedish National Archives Search Server
    
    Search the Riksarkivet database for historical documents and records.
    
    AVAILABLE TOOLS:
    
    🔍 BASIC SEARCH:
    - search_records() → Simple search with text, names, places, and date ranges
    
    🎯 ADVANCED SEARCH:
    - advanced_search() → All basic search features + faceted filtering (object types, provenance, institutions)
    
    SEARCH EXAMPLES:
    
    Basic Search:
    - search_records("kaffe") → Documents mentioning coffee
    - search_records("Nobel", year_min=1800, year_max=1920) → Nobel documents 1800-1920
    - search_records(name="Einstein", place="Stockholm") → Einstein references in Stockholm
    
    Advanced Search (includes all basic features + filters):
    - advanced_search("kyrkoböcker", object_type="Record", record_type="Volume") → Church records as volumes
    - advanced_search("Stockholm", provenance="GovernmentAuthority") → Government documents about Stockholm
    - advanced_search("Nobel", year_min=1800, year_max=1920, object_type="Agent") → Nobel as a person 1800-1920
    - advanced_search(place="Stockholm", archival_institution="Riksarkivet") → Stockholm content at Riksarkivet
    
    WORKFLOW:
    1. Start with search_records() for simple text/name/place queries
    2. Use advanced_search() when you need filtering by:
       - Object types (RecordSet, Record, Agent, Topography)
       - Record types (Volume, Dossier, Photography, etc.)
       - Provenance (GovernmentAuthority, Company, Person, etc.)
       - Specific archives or hierarchical places
    3. Both tools show available facets for further refinement
    4. Get PIDs from results → Use with IIIF tools for document access
    
    TIP: advanced_search() can do everything search_records() can do + more filtering options!
    """,
)

search_client = RiksarkivetSearchClient()

@search_mcp.prompt()
def test_prompt(
    string: Optional[str] = Field(description="Return string with hello world.", default=None),
) -> str:
    if string is None:
        return "Hello, world!"
    else:   
        return f"Hello, world! {string}"

@search_mcp.tool(
    name="search_records",
    description="Search Swedish National Archives for documents. ALWAYS extract keywords from user's question and provide them in the 'text' parameter. Example: user asks 'vad finns det om häxor?' → use text='häxor'",
    tags={"search", "basic"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Basic Search",
    },
)
async def search_records(
    text: str = Field(description="Search text to look for in documents.", default=""),
    name: str = Field(description="Search in names/titles (optional)", default=""),
    place: str = Field(description="Search in place references (optional)", default=""),
    year_min: Optional[int] = Field(description="Earliest year (e.g., 1800)", ge=0, le=9999, default=None),
    year_max: Optional[int] = Field(description="Latest year (e.g., 1920)", ge=0, le=9999, default=None),
    sort_by: Annotated[
        str,
        Field(
            description="Sort order: relevance, alphaAsc, alphaDesc, timeAsc, timeDesc"
        ),
    ] = "relevance",
    offset: Annotated[
        int,
        Field(description="Pagination offset (default: 0)", ge=0),
    ] = 0,
    max_results: Annotated[
        int,
        Field(description="Maximum results to return (default: 50)", ge=1, le=100),
    ] = 50,
    max_per_type: Annotated[
        int,
        Field(
            description="Max results to show per object type (default: 8)", ge=3, le=20
        ),
    ] = 8,
) -> str:
    """
    Search for documents in the Swedish National Archives. 
    
    Examples:
    - User asks "vad finns det om häxor?" → call with text="häxor"
    - User asks "Stockholm records" → call with place="Stockholm"
    """

    try:
        if not text.strip():
            return "❌ The 'text' parameter is required. Examples:\n• text='häxor' (search for witches)\n• text='Nobel' (search for Nobel-related content)\n• text='Stockholm' (search for Stockholm-related content)"

        try:
            sort_enum = SortOption(sort_by)
        except ValueError:
            return f"Invalid sort_by. Use: {', '.join([e.value for e in SortOption])}"

        results = await search_client.search_records(
            text=text,
            name=name,
            place=place,
            year_min=year_min,
            year_max=year_max,
            sort=sort_enum,
            offset=offset,
            max_results=max_results,
        )

        if not results.results:
            search_terms = [term for term in [text, name, place] if term]
            return f"No results found for '{', '.join(search_terms)}'. Try different keywords or use advanced_search() for filtering."

        search_parts = []
        if text:
            search_parts.append(f"text:'{text}'")
        if name:
            search_parts.append(f"name:'{name}'")
        if place:
            search_parts.append(f"place:'{place}'")
        if year_min or year_max:
            year_part = f"{year_min or '?'}-{year_max or '?'}"
            search_parts.append(f"years:{year_part}")

        search_desc = " | ".join(search_parts)

        info_lines = [
            f"🔍 Search Results: {search_desc}",
            f"📊 Found {results.total_hits:,} total hits (showing {results.hits} from offset {results.offset})",
            "",
        ]

        by_type = {}
        for result in results.results:
            obj_type = result.object_type
            if obj_type not in by_type:
                by_type[obj_type] = []
            by_type[obj_type].append(result)

        for obj_type, type_results in by_type.items():
            info_lines.append(f"📁 {obj_type} ({len(type_results)} results)")
            for result in type_results[:max_per_type]:
                info_lines.append(f"   • {result.caption}")
                info_lines.append(f"     PID: {result.id}")
                if result.reference_code:
                    info_lines.append(f"     Ref: {result.reference_code}")
                if result.metadata and result.metadata.date:
                    info_lines.append(f"     Date: {result.metadata.date}")
                if result.links and "image" in result.links:
                    info_lines.append("     🖼️ Digitized content available")

            if len(type_results) > max_per_type:
                info_lines.append(f"   ... and {len(type_results) - max_per_type} more")
            info_lines.append("")

        if results.facets:
            info_lines.append("🎯 Available filters (use advanced_search() to apply):")
            for facet in results.facets[:4]:
                top_values = facet.values[:3]
                values_text = ", ".join([f"{v.value} ({v.hits})" for v in top_values])
                info_lines.append(f"   {facet.name}: {values_text}")
            info_lines.append("")

        info_lines.extend(
            [
                "📋 Next steps:",
                "• Use advanced_search() for specific filtering by type, provenance, etc.",
                "• Use get_collection_info(pid) to explore a collection",
                "• Use get_all_manifests_from_pid(pid) to see image batches",
            ]
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Search error: {str(e)}")


@search_mcp.tool(
    name="advanced_search",
    description="Advanced search in Swedish National Archives with filtering. ALWAYS extract keywords from user's question and provide them in the 'text' parameter. Example: user asks 'vad finns det om häxor?' → use text='häxor'",
    tags={"search", "advanced"},
    annotations={"readOnlyHint": True, "title": "Advanced Search with Facets"},
)
async def advanced_search(
    text: str = Field(description="Search text to look for in documents.", default=""),
    name: str = Field(description="Search in names/titles (optional)", default=""),
    place: str = Field(description="Search in place references (optional)", default=""),
    year_min: Annotated[
        Optional[int],
        Field(description="Earliest year", ge=0, le=9999),
    ] = None,
    year_max: Annotated[
        Optional[int],
        Field(description="Latest year", ge=0, le=9999),
    ] = None,
    object_type: Annotated[
        Optional[str],
        Field(description="Object type: RecordSet, Record, Agent, Topography"),
    ] = None,
    record_type: str = Field(
        description="Record type: Volume, Dossier, Photography, MapDrawing, etc.", default=""
    ),
    provenance: Annotated[
        Optional[str],
        Field(description="Provenance: GovernmentAuthority, Company, Person, etc."),
    ] = None,
    archival_institution: str = Field(
        description="Archival institution (e.g., 'Riksarkivet i Stockholm')", default=""
    ),
    place_filter: str = Field(
        description="Hierarchical place filter (e.g., 'Sverige/Stockholms län')", default=""
    ),
    sort_by: Annotated[
        str,
        Field(
            description="Sort order: relevance, alphaAsc, alphaDesc, timeAsc, timeDesc"
        ),
    ] = "relevance",
    offset: Annotated[
        int,
        Field(description="Pagination offset (default: 0)", ge=0),
    ] = 0,
    max_results: Annotated[
        int,
        Field(description="Maximum results to return (default: 50)", ge=1, le=100),
    ] = 50,
    max_per_type: Annotated[
        int,
        Field(
            description="Max results to show per object type (default: 8)", ge=3, le=20
        ),
    ] = 8,
) -> str:
    """
    Advanced search with comprehensive filtering options using facets.
    Perfect for precise queries and research.
    """
    try:
        if not text.strip():
            return "❌ The 'text' parameter is required for advanced search. Examples:\n• text='häxor' (search for witches)\n• text='Nobel' (search for Nobel-related content)\n• text='Stockholm' (search for Stockholm-related content)"

        obj_type_enum = None
        if object_type:
            try:
                obj_type_enum = ObjectType(object_type)
            except ValueError:
                return f"Invalid object_type. Use: {', '.join([e.value for e in ObjectType])}"

        sort_enum = SortOption.RELEVANCE
        try:
            sort_enum = SortOption(sort_by)
        except ValueError:
            return f"Invalid sort_by. Use: {', '.join([e.value for e in SortOption])}"

        prov_enum = None
        if provenance:
            try:
                prov_enum = Provenance(provenance)
            except ValueError:
                return f"Invalid provenance. Use: {', '.join([e.value for e in Provenance])}"

        results = await search_client.search_records(
            text=text or None,
            name=name or None,
            place=place or None,
            year_min=year_min,
            year_max=year_max,
            object_type=obj_type_enum,
            record_type=record_type or None,
            provenance=prov_enum,
            archival_institution=archival_institution or None,
            place_filter=place_filter or None,
            sort=sort_enum,
            offset=offset,
            max_results=max_results,
        )

        if not results.results:
            filters_used = [
                f
                for f in [text, name, place, object_type, record_type, provenance]
                if f
            ]
            return f"No results found with your filters ({', '.join(filters_used)}). Try broader criteria."

        info_lines = [
            "🎯 Advanced Search Results",
            f"📊 {results.total_hits:,} total hits (showing {results.hits})",
            f"🔍 Query: {results.query}",
            "",
        ]

        by_type = {}
        for result in results.results:
            obj_type = result.object_type
            if obj_type not in by_type:
                by_type[obj_type] = []
            by_type[obj_type].append(result)

        for obj_type, type_results in by_type.items():
            info_lines.append(f"📁 {obj_type} ({len(type_results)} results)")
            for result in type_results[:max_per_type]:
                info_lines.append(f"   • {result.caption}")
                info_lines.append(f"     PID: {result.id}")
                info_lines.append(f"     Type: {result.object_type} → {result.type}")

                if result.metadata:
                    if result.metadata.reference_code:
                        info_lines.append(f"     Ref: {result.metadata.reference_code}")
                    if result.metadata.date:
                        info_lines.append(f"     Date: {result.metadata.date}")
                    if result.metadata.hierarchy:
                        hierarchy_path = " → ".join(
                            [h.caption for h in result.metadata.hierarchy[-2:]]
                        )
                        info_lines.append(f"     Path: {hierarchy_path}")

                if result.links and "image" in result.links:
                    info_lines.append("     🖼️ Digitized content available")

            if len(type_results) > max_per_type:
                info_lines.append(f"   ... and {len(type_results) - max_per_type} more")
            info_lines.append("")

        if results.facets:
            info_lines.append("🎯 Available facets for further refinement:")
            for facet in results.facets:
                if facet.values:
                    top_values = facet.values[:5]
                    values_text = ", ".join(
                        [f"{v.value} ({v.hits})" for v in top_values]
                    )
                    info_lines.append(f"   {facet.name}: {values_text}")
            info_lines.append("")

        info_lines.extend(
            [
                "📋 Next steps:",
                "• Refine further with additional facet parameters",
                "• Use get_collection_info(pid) to explore specific collections",
                "• Use get_all_manifests_from_pid(pid) to access digitized content",
            ]
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Advanced search failed: {str(e)}")
