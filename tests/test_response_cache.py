"""The scoped response cache: allowlisted search/browse tools are cached; the
stateful/App tools are not (caching them would break the viewer/pdf apps).
"""

from fastmcp import Client, FastMCP
from fastmcp.server.middleware.caching import CallToolSettings, ResponseCachingMiddleware
from key_value.aio.stores.memory import MemoryStore

from ra_mcp_server.server import CACHEABLE_TOOLS, create_server, setup_server


def _counter_server() -> tuple[FastMCP, dict[str, int]]:
    """A server with two tools that count calls: one cached, one not."""
    calls = {"cached": 0, "uncached": 0}
    mcp = FastMCP("cache-test")

    @mcp.tool
    def search_thing(q: str) -> str:  # name contains "search" -> in the allowlist
        calls["cached"] += 1
        return f"result-{q}-{calls['cached']}"

    @mcp.tool
    def get_state(view_id: str) -> str:  # NOT in the allowlist
        calls["uncached"] += 1
        return f"state-{calls['uncached']}"

    mcp.add_middleware(
        ResponseCachingMiddleware(
            cache_storage=MemoryStore(),
            call_tool_settings=CallToolSettings(included_tools=["search_thing"], ttl=300),
        )
    )
    return mcp, calls


async def test_allowlisted_tool_is_cached_on_identical_args():
    mcp, calls = _counter_server()
    async with Client(mcp) as c:
        r1 = (await c.call_tool("search_thing", {"q": "abc"})).content[0].text
        r2 = (await c.call_tool("search_thing", {"q": "abc"})).content[0].text
    # Second identical call served from cache -> handler ran once, same result.
    assert r1 == r2
    assert calls["cached"] == 1


async def test_different_args_are_not_a_cache_hit():
    mcp, calls = _counter_server()
    async with Client(mcp) as c:
        await c.call_tool("search_thing", {"q": "abc"})
        await c.call_tool("search_thing", {"q": "xyz"})
    assert calls["cached"] == 2  # different args -> both executed


async def test_non_allowlisted_tool_is_never_cached():
    mcp, calls = _counter_server()
    async with Client(mcp) as c:
        r1 = (await c.call_tool("get_state", {"view_id": "v"})).content[0].text
        r2 = (await c.call_tool("get_state", {"view_id": "v"})).content[0].text
    # A polled state tool must return fresh every call, never cached.
    assert r1 != r2
    assert calls["uncached"] == 2


def test_allowlist_matches_the_readonly_search_rule():
    # Drift guard: CACHEABLE_TOOLS must equal exactly the readOnly tools whose name
    # contains "search" or is "browse_document" on the fully composed server. When a
    # new dataset MCP is added, this fails until its search tool is added above.
    from ra_mcp_server.server import AVAILABLE_MODULES

    mods = list(AVAILABLE_MODULES)
    server = create_server(mods)
    setup_server(server, mods)

    import asyncio

    async def _names() -> set[str]:
        async with Client(server) as c:
            tools = await c.list_tools()
        return {t.name for t in tools if getattr(t.annotations, "readOnlyHint", None) and ("search" in t.name or t.name == "browse_document")}

    expected = asyncio.run(_names())
    assert set(CACHEABLE_TOOLS) == expected, f"allowlist drift: missing={expected - set(CACHEABLE_TOOLS)}, extra={set(CACHEABLE_TOOLS) - expected}"
