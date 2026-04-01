"""FastMCP server definition for Sjömanshus seamen's records search tools."""

from fastmcp import FastMCP

from .liggare_tool import register_liggare_tool
from .matrikel_tool import register_matrikel_tool


sjomanshus_mcp = FastMCP(
    name="ra-sjomanshus-mcp",
    instructions=(
        "Search Swedish seamen's house records (Sjömanshus) — 688,000+ records covering voyages "
        "and registrations from the 1700s to 1900s. "
        "Use search_liggare for voyage records (637K) with ship, rank, and port filters. "
        "Use search_matrikel for registration records (51K) with birth and parish details."
    ),
)

register_liggare_tool(sjomanshus_mcp)
register_matrikel_tool(sjomanshus_mcp)
