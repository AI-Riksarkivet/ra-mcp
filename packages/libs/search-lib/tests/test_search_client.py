"""Tests for search API client with mocked HTTP."""

import httpx
import pytest
import respx

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_search_lib.config import SEARCH_API_BASE_URL
from ra_mcp_search_lib.search_client import SearchClient


@respx.mock(assert_all_called=False)
async def test_search_transcribed_success(respx_mock, search_response_json):
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(transcribed_text="trolldom", limit=50, offset=0)
    finally:
        await http.aclose()

    # Real data from Riksarkivet Search API
    assert result.total_hits == 42
    assert len(result.items) == 2
    assert result.items[0].id == "yGQHHgW0hQVANqVjuw6fZ1"
    assert result.items[0].metadata.reference_code == "SE/RA/310187/1"
    assert result.items[0].transcribed_text is not None
    assert len(result.items[0].transcribed_text.snippets) == 3
    assert result.items[0].transcribed_text.num_total == 12


@respx.mock(assert_all_called=False)
async def test_search_metadata_success(respx_mock, search_response_json):
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(text="Stockholm", only_digitised_materials=False)
    finally:
        await http.aclose()

    assert result.total_hits == 42
    # Verify 'text' param was sent (not 'transcribed_text')
    call = respx_mock.calls[0]
    assert "text" in str(call.request.url)


@respx.mock(assert_all_called=False)
async def test_search_with_filters(respx_mock, search_response_json):
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(
            text="trolldom",
            only_digitised_materials=False,
            year_min=1669,
            year_max=1670,
            name="Gertrud",
            place="Mora",
        )
    finally:
        await http.aclose()

    assert result.total_hits == 42
    call = respx_mock.calls[0]
    url_str = str(call.request.url)
    assert "year_min=1669" in url_str
    assert "year_max=1670" in url_str
    assert "name=Gertrud" in url_str
    assert "place=Mora" in url_str


async def test_search_no_params_raises():
    http = HTTPClient()
    client = SearchClient(http)
    with pytest.raises(ValueError, match="Must provide at least one search parameter"):
        await client.search()


async def test_search_transcribed_without_digitised_raises():
    http = HTTPClient()
    client = SearchClient(http)
    with pytest.raises(ValueError, match="transcribed_text search requires only_digitised_materials=True"):
        await client.search(transcribed_text="trolldom", only_digitised_materials=False)


@respx.mock(assert_all_called=False)
async def test_search_snippet_limiting(respx_mock, search_response_json):
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(transcribed_text="trolldom", max_snippets_per_record=1)
    finally:
        await http.aclose()

    # First record originally had 3 snippets, should be limited to 1
    assert result.items[0].transcribed_text is not None
    assert len(result.items[0].transcribed_text.snippets) == 1


@respx.mock(assert_all_called=False)
async def test_search_count_snippets(respx_mock, search_response_json):
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(transcribed_text="trolldom")
    finally:
        await http.aclose()

    # 3 snippets in first record + 1 in second = 4
    assert result.count_snippets() == 4


@respx.mock(assert_all_called=False)
async def test_search_name_only(respx_mock, search_response_json):
    """Search with only name parameter should work."""
    respx_mock.get(SEARCH_API_BASE_URL).mock(return_value=httpx.Response(200, json=search_response_json))

    http = HTTPClient()
    client = SearchClient(http)
    try:
        result = await client.search(name="Gertrud", only_digitised_materials=False)
    finally:
        await http.aclose()

    assert result.total_hits == 42
