"""FastMCP server definition for Aktiebolag company and board member search tools."""

from fastmcp import FastMCP

from .bolag_tool import register_bolag_tool
from .styrelse_tool import register_styrelse_tool


aktiebolag_mcp = FastMCP(
    name="ra-aktiebolag-mcp",
    instructions=(
        "Search Swedish joint-stock company records (Aktiebolag) 1901-1935 — 12,500 companies with "
        ">100,000 kr capital and 49,000 board members. "
        "Use search_bolag for companies with name, purpose, address, directors, and board members. "
        "Use search_styrelse for board members with name, title, gender, and company affiliation."
    ),
)

register_bolag_tool(aktiebolag_mcp)
register_styrelse_tool(aktiebolag_mcp)
