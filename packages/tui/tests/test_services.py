"""Tests for the ArchiveService facade."""

from unittest.mock import AsyncMock, patch

from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_search_lib.models import SearchResult

from ra_mcp_tui.services import ArchiveService

from conftest import make_browse_result, make_page_context, make_search_result


def test_search_transcribed_delegates_to_operations():
    service = ArchiveService()
    expected = make_search_result(keyword="trolldom")
    with patch.object(service._search, "search", new_callable=AsyncMock, return_value=expected) as mock:
        result = service.search_transcribed("trolldom", offset=0, limit=25)

    mock.assert_awaited_once_with(keyword="trolldom", transcribed_only=True, offset=0, limit=25)
    assert isinstance(result, SearchResult)
    assert result.keyword == "trolldom"


def test_search_metadata_delegates_to_operations():
    service = ArchiveService()
    expected = make_search_result(keyword="Stockholm")
    with patch.object(service._search, "search", new_callable=AsyncMock, return_value=expected) as mock:
        result = service.search_metadata("Stockholm", offset=10, limit=50)

    mock.assert_awaited_once_with(keyword="Stockholm", transcribed_only=False, only_digitised=False, offset=10, limit=50)
    assert result.keyword == "Stockholm"


def test_browse_document_delegates_to_operations():
    service = ArchiveService()
    expected = make_browse_result()
    with patch.object(service._browse, "browse_document", new_callable=AsyncMock, return_value=expected) as mock:
        result = service.browse_document("SE/RA/310187/1", pages="1-5", highlight_term="test", max_pages=5)

    mock.assert_awaited_once_with(reference_code="SE/RA/310187/1", pages="1-5", highlight_term="test", max_pages=5)
    assert isinstance(result, BrowseResult)
    assert len(result.contexts) == 3


def test_search_transcribed_default_params():
    service = ArchiveService()
    expected = make_search_result()
    with patch.object(service._search, "search", new_callable=AsyncMock, return_value=expected) as mock:
        service.search_transcribed("test")

    mock.assert_awaited_once_with(keyword="test", transcribed_only=True, offset=0, limit=25)


def test_browse_document_default_params():
    service = ArchiveService()
    expected = make_browse_result()
    with patch.object(service._browse, "browse_document", new_callable=AsyncMock, return_value=expected) as mock:
        service.browse_document("SE/RA/310187/1")

    mock.assert_awaited_once_with(reference_code="SE/RA/310187/1", pages="1-20", highlight_term=None, max_pages=20)


def test_service_reuses_event_loop():
    """The dedicated event loop should stay running across multiple calls."""
    service = ArchiveService()
    assert service._loop.is_running()
    assert service._thread.is_alive()

    expected = make_search_result()
    with patch.object(service._search, "search", new_callable=AsyncMock, return_value=expected):
        service.search_transcribed("a")
        service.search_transcribed("b")

    assert service._loop.is_running()
