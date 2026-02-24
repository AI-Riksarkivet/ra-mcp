"""Tests for search operations with mocked client."""

from unittest.mock import AsyncMock, patch

import pytest

from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_search.models import Metadata, PageInfo, RecordsResponse, SearchRecord, Snippet, TranscribedText
from ra_mcp_search.search_operations import SearchOperations


def _make_records_response(total_hits: int = 10, num_records: int = 2) -> RecordsResponse:
    """Build a minimal RecordsResponse for testing."""
    items = [
        SearchRecord(
            id=f"SE/RA/TEST/{i}",
            object_type="Record",
            type="Volume",
            caption=f"Test Record {i}",
            metadata=Metadata(reference_code=f"SE/RA/TEST/{i}"),
            transcribed_text=TranscribedText(
                num_total=3,
                snippets=[Snippet(text=f"Snippet {j} of record {i}", score=0.9 - j * 0.1, pages=[PageInfo(id=f"_{j:05d}")]) for j in range(3)],
            ),
        )
        for i in range(num_records)
    ]
    return RecordsResponse(total_hits=total_hits, items=items, hits=num_records, offset=0)


async def test_search_transcribed():
    http = HTTPClient()
    ops = SearchOperations(http)

    mock_response = _make_records_response(total_hits=42, num_records=2)

    with patch.object(ops.search_api, "search", new_callable=AsyncMock, return_value=mock_response):
        result = await ops.search(keyword="trolldom", transcribed_only=True)

    assert result.total_hits == 42
    assert result.keyword == "trolldom"
    assert len(result.items) == 2
    assert result.offset == 0


async def test_search_metadata():
    http = HTTPClient()
    ops = SearchOperations(http)

    mock_response = _make_records_response(total_hits=100, num_records=1)

    with patch.object(ops.search_api, "search", new_callable=AsyncMock, return_value=mock_response) as mock_search:
        result = await ops.search(keyword="Stockholm", transcribed_only=False, only_digitised=False)

    # Verify that text (not transcribed_text) was passed to the client
    mock_search.assert_called_once()
    call_kwargs = mock_search.call_args[1]
    assert call_kwargs["text"] == "Stockholm"
    assert call_kwargs["transcribed_text"] is None
    assert call_kwargs["only_digitised_materials"] is False
    assert result.total_hits == 100


async def test_search_error_propagation():
    http = HTTPClient()
    ops = SearchOperations(http)

    with (
        patch.object(ops.search_api, "search", new_callable=AsyncMock, side_effect=TimeoutError("Request timeout")),
        pytest.raises(TimeoutError, match="Request timeout"),
    ):
        await ops.search(keyword="trolldom")


async def test_search_transcribed_convenience():
    http = HTTPClient()
    ops = SearchOperations(http)

    mock_response = _make_records_response(total_hits=5, num_records=1)

    with patch.object(ops.search_api, "search", new_callable=AsyncMock, return_value=mock_response) as mock_search:
        result = await ops.search_transcribed(keyword="häxa", offset=50, limit=25)

    mock_search.assert_called_once()
    call_kwargs = mock_search.call_args[1]
    assert call_kwargs["transcribed_text"] == "häxa"
    assert call_kwargs["only_digitised_materials"] is True
    assert call_kwargs["offset"] == 50
    assert call_kwargs["limit"] == 25
    assert result.total_hits == 5


async def test_search_with_filters():
    http = HTTPClient()
    ops = SearchOperations(http)

    mock_response = _make_records_response(total_hits=3, num_records=1)

    with patch.object(ops.search_api, "search", new_callable=AsyncMock, return_value=mock_response) as mock_search:
        await ops.search(
            keyword="trolldom",
            year_min=1669,
            year_max=1670,
            name="Gertrud",
            place="Mora",
            sort="timeAsc",
        )

    call_kwargs = mock_search.call_args[1]
    assert call_kwargs["year_min"] == 1669
    assert call_kwargs["year_max"] == 1670
    assert call_kwargs["name"] == "Gertrud"
    assert call_kwargs["place"] == "Mora"
    assert call_kwargs["sort"] == "timeAsc"
