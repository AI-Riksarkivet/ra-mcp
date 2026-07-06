"""Integration tests for MCP tools using FastMCP's in-memory test client."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

import ra_mcp_viewer_mcp.state as _state_mod
from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_viewer_mcp import viewer_mcp as mcp


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def _reset_viewer_state():
    _state_mod._latest_view_by_session.clear()
    yield
    _state_mod._latest_view_by_session.clear()


FAKE_IMAGE_URL = "https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/1500,/0/default.jpg"


@pytest.fixture()
def alto_text_layer() -> dict:
    """A realistic parsed text layer dict from the ALTO fixture."""
    from ra_mcp_xml.parser import parse_alto_xml

    xml = (FIXTURES / "451511_1512_01_alto.xml").read_text()
    data = parse_alto_xml(xml)
    return {
        "textLines": [line.model_dump() for line in data.text_lines],
        "pageWidth": data.page_width,
        "pageHeight": data.page_height,
    }


@pytest.fixture()
def fake_browse_result() -> BrowseResult:
    """A fake BrowseResult with one page context."""
    return BrowseResult(
        contexts=[
            PageContext(
                page_number=7,
                page_id="7",
                reference_code="SE/RA/310187/1",
                full_text="skäligt sin emillan förafskeda, och det eftter Kongl. Mommouth",
                alto_url="https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml",
                image_url="https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/max/0/default.jpg",
                bildvisning_url="https://sok.riksarkivet.se/bildvisning/R0001203_00007",
            ),
        ],
        reference_code="SE/RA/310187/1",
        pages_requested="7",
        manifest_id="R0001203",
    )


@pytest.fixture()
def mock_fetchers(alto_text_layer, fake_browse_result):
    """Patch all async fetchers and BrowseOperations to avoid real HTTP calls."""
    with (
        patch("ra_mcp_viewer_mcp.tools.fetch_and_parse_text_layer", new_callable=AsyncMock) as mock_text,
        patch("ra_mcp_viewer_mcp.tools.build_page_data", new_callable=AsyncMock) as mock_page,
        patch("ra_mcp_viewer_mcp.resolve.BrowseOperations") as mock_browse_cls,
    ):
        mock_text.return_value = alto_text_layer
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": FAKE_IMAGE_URL, "textLayer": alto_text_layer},
            [],
        )
        mock_browse = AsyncMock()
        mock_browse.browse_document.return_value = fake_browse_result
        mock_browse_cls.return_value = mock_browse
        yield {"text_layer": mock_text, "page": mock_page, "browse": mock_browse}


# ── view_document ─────────────────────────────────────────────────────


async def test_view_document_opens_viewer(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7"},
        )

    assert not result.is_error
    text = result.content[0].text
    assert "1 page(s)" in text
    assert "SE/RA/310187/1" in text
    assert result.structured_content["image_urls"]
    assert result.structured_content["text_layer_urls"]


async def test_view_document_with_highlight_term(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7", "highlight_term": "trolldom"},
        )

    assert not result.is_error
    assert result.structured_content["highlight_term"] == "trolldom"


async def test_view_document_empty_reference_code(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "", "pages": "1"},
        )

    text = result.content[0].text
    assert "empty" in text.lower()


# ── get_viewer_state (polling) ────────────────────────────────────────


async def test_viewer_state_multi_user_isolation(mock_fetchers):
    """Two viewers get independent state — updating one does not affect the other."""
    async with Client(mcp) as client:
        # User A opens a document
        doc_a = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7"},
        )
        view_id_a = doc_a.structured_content["view_id"]

        # User B opens a different document
        doc_b = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/other.jpg"],
                "text_layer_urls": ["https://example.com/other.xml"],
            },
        )
        view_id_b = doc_b.structured_content["view_id"]

        assert view_id_a != view_id_b

        # Update highlight on the latest viewer (B)
        await client.call_tool("viewer_set_highlight", {"highlight_term": "test"})

        # User A's state should be unchanged
        state_a = await client.call_tool("get_viewer_state", {"view_id": view_id_a})
        assert state_a.structured_content["highlight_term"] == ""
        assert state_a.structured_content["version"] == 1

        # User B's state should have the highlight
        state_b = await client.call_tool("get_viewer_state", {"view_id": view_id_b})
        assert state_b.structured_content["highlight_term"] == "test"
        assert state_b.structured_content["version"] == 2


async def test_get_viewer_state_returns_version(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7"},
        )
        view_id = doc.structured_content["view_id"]

        result = await client.call_tool("get_viewer_state", {"view_id": view_id})
        assert result.structured_content["version"] == 1
        assert len(result.structured_content["image_urls"]) == 1
        assert result.structured_content["reference_code"] == "SE/RA/310187/1"


async def test_get_viewer_state_updates_on_view_document_urls(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml", ""],
            },
        )
        view_id = doc.structured_content["view_id"]

        result = await client.call_tool("get_viewer_state", {"view_id": view_id})
        assert result.structured_content["version"] >= 1
        assert len(result.structured_content["image_urls"]) == 2
        assert result.structured_content["reference_code"] == ""


# ── viewer_set_highlight ──────────────────────────────────────────────


async def test_viewer_set_highlight_updates_state(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        result = await client.call_tool("viewer_set_highlight", {"highlight_term": "trolldom"})

    assert not result.is_error
    assert "Highlighting" in result.content[0].text

    async with Client(mcp) as client:
        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
    assert state.structured_content["highlight_term"] == "trolldom"
    assert state.structured_content["version"] == 2


async def test_viewer_set_highlight_without_viewer(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool("viewer_set_highlight", {"highlight_term": "test"})

    text = result.content[0].text
    assert "no document" in text.lower()


async def test_viewer_set_highlight_clear(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        await client.call_tool("viewer_set_highlight", {"highlight_term": ""})

        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
    assert state.structured_content["highlight_term"] == ""


# ── viewer_navigate ──────────────────────────────────────────────────


async def test_viewer_navigate_updates_pages(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        result = await client.call_tool("viewer_navigate", {"reference_code": "SE/RA/310187/1", "pages": "8"})

    assert not result.is_error
    assert "Navigated" in result.content[0].text

    async with Client(mcp) as client:
        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
    assert state.structured_content["version"] == 2


async def test_viewer_navigate_with_highlight(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        await client.call_tool(
            "viewer_navigate",
            {"reference_code": "SE/RA/310187/1", "pages": "7", "highlight_term": "Stockholm"},
        )
        state = await client.call_tool("get_viewer_state", {"view_id": view_id})

    assert state.structured_content["highlight_term"] == "Stockholm"


# ── viewer_navigate_urls ──────────────────────────────────────────────


async def test_viewer_navigate_urls_updates_pages(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml"],
            },
        )
        view_id = doc.structured_content["view_id"]
        result = await client.call_tool(
            "viewer_navigate_urls",
            {
                "image_urls": ["https://example.com/p3.jpg", "https://example.com/p4.jpg"],
                "text_layer_urls": ["https://example.com/p3.xml", ""],
            },
        )

    assert not result.is_error
    assert "Navigated" in result.content[0].text

    async with Client(mcp) as client:
        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
    assert state.structured_content["version"] == 2
    assert len(state.structured_content["image_urls"]) == 2


async def test_viewer_navigate_urls_resets_stale_bildvisning(mock_fetchers):
    # view_document populates bildvisning_urls + document_info; navigating to raw URLs
    # must clear them so the previous document's viewer links / info don't map onto the
    # new pages.
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        await client.call_tool(
            "viewer_navigate_urls",
            {
                "image_urls": ["https://example.com/p3.jpg", "https://example.com/p4.jpg"],
                "text_layer_urls": ["https://example.com/p3.xml", ""],
            },
        )
        state = await client.call_tool("get_viewer_state", {"view_id": view_id})

    sc = state.structured_content
    assert sc["bildvisning_urls"] == ["", ""]  # not the old document's bildvisning URL
    assert sc["document_info"] == ""


# ── view_id survives session-pointer loss (the "No viewer open" regression) ──
#
# The deployed transport does NOT keep a stable MCP session_id across separate tool
# calls, so the per-session "active view" pointer set by view_document isn't found by a
# later mutation call — every control tool returned "No viewer is open". These tests
# reproduce that by clearing the pointer mid-flight, and prove the explicit view_id path
# targets the view regardless of session. (The other tests here can't catch it: they
# open+mutate in one in-process Client session, where the pointer is stable.)


async def test_resolve_state_prefers_view_id_over_session_pointer():
    """State-level proof: with the session pointer gone, get_active_state() fails but an
    explicit view_id still resolves; an unknown id raises instead of inventing a blank state."""
    from ra_mcp_viewer_mcp.models import ViewerState
    from ra_mcp_viewer_mcp.state import get_active_state, put_state, require_state, resolve_state

    await put_state(ViewerState(view_id="vid-abc", image_urls=["u"]))
    _state_mod._latest_view_by_session.clear()  # simulate the transport losing the session pointer

    with pytest.raises(LookupError):
        await get_active_state()  # the old path — reproduces "No viewer is open"
    with pytest.raises(LookupError):
        await resolve_state(None)  # no view_id → same failure

    got = await resolve_state("vid-abc")  # explicit view_id → works regardless of session
    assert got.view_id == "vid-abc"

    with pytest.raises(LookupError):
        await require_state("no-such-view")  # unknown id raises, never a blank default


async def test_mutation_with_view_id_survives_session_loss(mock_fetchers):
    """Tool-level: after the session pointer is lost, viewer_go_to_page fails WITHOUT a
    view_id (the bug) but succeeds WITH one (the fix)."""
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        assert f"view_id: {view_id}" in doc.content[0].text  # surfaced so the model can pass it back

        _state_mod._latest_view_by_session.clear()  # deployed transport: pointer not shared across calls

        no_id = await client.call_tool("viewer_go_to_page", {"page": 1})
        assert "no viewer" in no_id.content[0].text.lower()  # reproduces the reported bug

        ok = await client.call_tool("viewer_go_to_page", {"page": 1, "view_id": view_id})
        assert not ok.is_error and "Navigated" in ok.content[0].text  # the fix

        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
        assert state.structured_content["go_to_page"] == 0  # page 1 → 0-based index


async def test_set_highlight_with_view_id_survives_session_loss(mock_fetchers):
    async with Client(mcp) as client:
        doc = await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        view_id = doc.structured_content["view_id"]
        _state_mod._latest_view_by_session.clear()

        ok = await client.call_tool("viewer_set_highlight", {"highlight_term": "trolldom", "view_id": view_id})
        assert not ok.is_error

        state = await client.call_tool("get_viewer_state", {"view_id": view_id})
        assert state.structured_content["highlight_term"] == "trolldom"


# ── view_document_urls ────────────────────────────────────────────────


async def test_view_document_urls_returns_structured_content(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": [
                    "https://lbiiif.riksarkivet.se/arkis!30002056_00010/full/max/0/default.jpg",
                    "https://lbiiif.riksarkivet.se/arkis!30002056_00011/full/max/0/default.jpg",
                ],
                "text_layer_urls": [
                    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00010.xml",
                    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00011.xml",
                ],
            },
        )

    assert not result.is_error
    text = result.content[0].text
    assert "2 page(s)" in text
    sc = result.structured_content
    assert len(sc["image_urls"]) == 2
    assert len(sc["text_layer_urls"]) == 2
    assert sc["page_numbers"] == [1, 2]
    assert sc["reference_code"] == ""


async def test_view_document_urls_with_highlight_term(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/page1.jpg"],
                "text_layer_urls": ["https://example.com/page1.xml"],
                "highlight_term": "trolldom",
            },
        )

    assert not result.is_error
    assert result.structured_content["highlight_term"] == "trolldom"


async def test_view_document_urls_mismatched_lengths(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/page1.jpg", "https://example.com/page2.jpg"],
                "text_layer_urls": ["https://example.com/page1.xml"],
            },
        )

    text = result.content[0].text
    assert "mismatched" in text.lower()


async def test_view_document_urls_empty_image_urls(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": [],
                "text_layer_urls": [],
            },
        )

    text = result.content[0].text
    assert "empty" in text.lower()


async def test_view_document_urls_with_empty_text_layers(mock_fetchers):
    """Pages without transcription should use empty string in text_layer_urls."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml", ""],
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["text_layer_urls"][1] == ""


# ── load_page ─────────────────────────────────────────────────────────


async def test_load_page_returns_structured_content(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load_page",
            {
                "image_url": "https://example.com/img.jpg",
                "text_layer_url": "https://example.com/alto.xml",
                "page_index": 0,
            },
        )

    assert not result.is_error
    page = result.structured_content["page"]
    assert page["index"] == 0
    assert "imageDataUrl" in page
    assert "textLayer" in page
    assert isinstance(page["textLayer"]["textLines"], list)


# ── load_thumbnails ──────────────────────────────────────────────────


async def test_load_thumbnails_returns_bounded_iiif_urls():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load_thumbnails",
            {
                "image_urls": [
                    "https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/max/0/default.jpg",
                    "https://lbiiif.riksarkivet.se/arkis!R0001203_00008/full/max/0/default.jpg",
                ],
                "page_indices": [0, 1],
            },
        )

    assert not result.is_error
    thumbnails = result.structured_content["thumbnails"]
    assert len(thumbnails) == 2
    assert thumbnails[0]["dataUrl"] == "https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/150,/0/default.jpg"
    assert all(not t["dataUrl"].startswith("data:") for t in thumbnails)


# ── Error handling ───────────────────────────────────────────────────


async def test_load_page_handles_fetch_error():
    """Bad URL should produce an error in the page data, not crash the tool."""
    with patch("ra_mcp_viewer_mcp.tools.build_page_data", new_callable=AsyncMock) as mock_page:
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": "", "textLayer": {"textLines": [], "pageWidth": 0, "pageHeight": 0}},
            ["Page 1 image: connection refused"],
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "load_page",
                {
                    "image_url": "https://bad-url.example.com/img.jpg",
                    "text_layer_url": "",
                    "page_index": 0,
                },
            )

    assert not result.is_error
    assert "Errors" in result.content[0].text


# ── search_all_pages ─────────────────────────────────────────────────


async def test_search_all_pages_returns_matches(mock_fetchers):
    """Searching for a term that exists in the fixture text layer should return matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml", "https://example.com/alto2.xml"],
                "term": "Mommouth",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] > 0
    assert len(sc["pageMatches"]) > 0
    for m in sc["pageMatches"]:
        assert "pageIndex" in m
        assert "matchCount" in m
        assert m["matchCount"] > 0


async def test_search_all_pages_no_matches(mock_fetchers):
    """Searching for a term not in the fixture should return zero matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "xyznonexistentterm",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] == 0
    assert sc["pageMatches"] == []


async def test_search_all_pages_empty_term(mock_fetchers):
    """Empty search term should return early with zero matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] == 0
    assert sc["pageMatches"] == []


async def test_search_all_pages_skips_empty_urls(mock_fetchers):
    """Empty string URLs should be skipped without error."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["", "https://example.com/alto1.xml", ""],
                "term": "Mommouth",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] > 0
    # Only the valid URL (index 1) should appear in matches
    page_indices = [m["pageIndex"] for m in sc["pageMatches"]]
    assert 0 not in page_indices  # empty URL skipped
    assert 1 in page_indices


async def test_search_all_pages_case_insensitive(mock_fetchers):
    """Search should be case-insensitive."""
    async with Client(mcp) as client:
        result_lower = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "mommouth",
            },
        )
        result_upper = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "MOMMOUTH",
            },
        )

    assert result_lower.structured_content["totalMatches"] == result_upper.structured_content["totalMatches"]
    assert result_lower.structured_content["totalMatches"] > 0
