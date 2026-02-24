"""Tests for browse operations with mocked clients."""

from unittest.mock import AsyncMock, patch

from ra_mcp_browse.browse_operations import BrowseOperations
from ra_mcp_browse.models import OAIPMHMetadata, PageContext
from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_xml import TextLayer


REFERENCE_CODE = "SE/RA/310187/1"
MANIFEST_ID = "R0001203"
NAD_LINK = f"https://sok.riksarkivet.se/bildvisning/{MANIFEST_ID}"


def _make_metadata(*, nad_link: str | None = NAD_LINK) -> OAIPMHMetadata:
    return OAIPMHMetadata(identifier=REFERENCE_CODE, nad_link=nad_link, title="Test doc")


def _make_page_context(page_number: int, text: str = "some text") -> PageContext:
    return PageContext(
        page_number=page_number,
        page_id=str(page_number),
        reference_code=REFERENCE_CODE,
        full_text=text,
        alto_url=f"https://sok.riksarkivet.se/dokument/alto/R000/{MANIFEST_ID}/{MANIFEST_ID}_{page_number:05d}.xml",
        image_url=f"https://lbiiif.riksarkivet.se/arkis!{MANIFEST_ID}_{page_number:05d}/full/max/0/default.jpg",
        bildvisning_url=f"https://sok.riksarkivet.se/bildvisning/{MANIFEST_ID}_{page_number:05d}",
    )


async def test_browse_document_success():
    http = HTTPClient()
    ops = BrowseOperations(http)

    mock_metadata = _make_metadata()
    mock_pages = [_make_page_context(1), _make_page_context(2)]

    with (
        patch.object(ops.oai_client, "get_metadata", new_callable=AsyncMock, return_value=mock_metadata),
        patch.object(ops.oai_client, "manifest_id_from_metadata", return_value=MANIFEST_ID),
        patch.object(ops, "_fetch_page_contexts", new_callable=AsyncMock, return_value=mock_pages),
    ):
        result = await ops.browse_document(REFERENCE_CODE, "1-2")

    assert result.reference_code == REFERENCE_CODE
    assert result.manifest_id == MANIFEST_ID
    assert len(result.contexts) == 2
    assert result.oai_metadata is not None
    assert result.oai_metadata.title == "Test doc"


async def test_browse_document_no_manifest():
    """Non-digitised document: no manifest ID -> empty contexts."""
    http = HTTPClient()
    ops = BrowseOperations(http)

    mock_metadata = _make_metadata(nad_link=None)

    with (
        patch.object(ops.oai_client, "get_metadata", new_callable=AsyncMock, return_value=mock_metadata),
        patch.object(ops.oai_client, "manifest_id_from_metadata", return_value=None),
    ):
        result = await ops.browse_document(REFERENCE_CODE, "1-5")

    assert result.contexts == []
    assert result.manifest_id is None
    assert result.oai_metadata is not None


async def test_browse_document_early_exit():
    """3 consecutive ALTO 404s should stop fetching."""
    http = HTTPClient()
    ops = BrowseOperations(http)

    mock_metadata = _make_metadata()

    # alto_client.fetch_content returns None for every page (simulating 404)
    with (
        patch.object(ops.oai_client, "get_metadata", new_callable=AsyncMock, return_value=mock_metadata),
        patch.object(ops.oai_client, "manifest_id_from_metadata", return_value=MANIFEST_ID),
        patch.object(ops.alto_client, "fetch_content", new_callable=AsyncMock, return_value=None) as mock_alto,
    ):
        result = await ops.browse_document(REFERENCE_CODE, "1-10")

    assert result.contexts == []
    # Should have stopped after 3 consecutive failures, not tried all 10 pages
    assert mock_alto.call_count == 3


async def test_browse_document_empty_pages_counted():
    """Blank pages (empty string content) are still returned as contexts."""
    http = HTTPClient()
    ops = BrowseOperations(http)

    mock_metadata = _make_metadata()
    blank_page = _make_page_context(1, text="")

    with (
        patch.object(ops.oai_client, "get_metadata", new_callable=AsyncMock, return_value=mock_metadata),
        patch.object(ops.oai_client, "manifest_id_from_metadata", return_value=MANIFEST_ID),
        patch.object(ops, "_fetch_page_contexts", new_callable=AsyncMock, return_value=[blank_page]),
    ):
        result = await ops.browse_document(REFERENCE_CODE, "1")

    assert len(result.contexts) == 1
    assert result.contexts[0].full_text == ""


async def test_fetch_page_contexts_resets_failure_counter():
    """A successful page after failures should reset the consecutive failure counter."""
    http = HTTPClient()
    ops = BrowseOperations(http)

    # Simulate: page 1 fails, page 2 fails, page 3 succeeds, page 4 fails, page 5 fails, page 6 fails
    call_count = 0

    async def mock_fetch_content(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 3:  # page 3 succeeds
            return TextLayer(text_lines=[], page_width=0, page_height=0, full_text="text on page 3")
        return None

    with patch.object(ops.alto_client, "fetch_content", side_effect=mock_fetch_content):
        result = await ops._fetch_page_contexts(MANIFEST_ID, "1-6", 20, REFERENCE_CODE, None)

    # Page 3 succeeded, so we should get 1 context
    assert len(result) == 1
    # After page 3, failures 4,5,6 would hit the 3-consecutive limit but since we
    # already have results (page_contexts is not empty), early exit doesn't trigger
    assert call_count == 6
