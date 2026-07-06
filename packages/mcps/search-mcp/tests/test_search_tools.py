"""Tests for ra-mcp-search-mcp tools."""

from fastmcp import Client

from ra_mcp_search_mcp.tools import search_mcp


def test_search_mcp_has_name() -> None:
    assert search_mcp.name == "ra-search-mcp"


async def test_transcribed_rejects_malformed_query() -> None:
    """A broken Boolean query must be rejected up front, not sent to the API."""
    async with Client(search_mcp) as client:
        result = await client.call_tool("transcribed", {"keyword": "(((", "offset": 0})
    assert "Unbalanced" in result.content[0].text


async def test_transcribed_rejects_oversized_limit() -> None:
    """An absurd limit is bounded client-side with a clear message, not an opaque HTTP 400."""
    async with Client(search_mcp) as client:
        result = await client.call_tool("transcribed", {"keyword": "Stockholm", "offset": 0, "limit": 999999})
    assert "limit must be <=" in result.content[0].text
