"""Tests for IIIF client with mocked HTTP."""

import json

import httpx
import respx

from ra_mcp_browse.clients import IIIFClient
from ra_mcp_browse.config import COLLECTION_API_BASE_URL
from ra_mcp_common.utils.http_client import HTTPClient


PID = "R0001203"
COLLECTION_URL = f"{COLLECTION_API_BASE_URL}/{PID}"


@respx.mock(assert_all_called=False)
async def test_get_collection_success(respx_mock, iiif_collection_json):
    respx_mock.get(COLLECTION_URL).mock(return_value=httpx.Response(200, json=json.loads(iiif_collection_json)))

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.get_collection(PID)
    finally:
        await http.aclose()

    assert result is not None
    assert result.label == "Trolldomskommissionen i Mora"
    # Only Manifest items should be returned, not Canvas
    assert len(result.manifests) == 2
    assert result.manifests[0].id == "arkis!R0001203"
    assert result.manifests[1].id == "arkis!R0001204"


@respx.mock(assert_all_called=False)
async def test_get_collection_not_found(respx_mock):
    respx_mock.get(COLLECTION_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.get_collection(PID)
    finally:
        await http.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_get_collection_empty_items(respx_mock):
    respx_mock.get(COLLECTION_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": COLLECTION_URL,
                "type": "Collection",
                "label": {"sv": ["Tomt arkiv"]},
                "items": [],
            },
        )
    )

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.get_collection(PID)
    finally:
        await http.aclose()

    assert result is not None
    assert result.manifests == []
    assert result.label == "Tomt arkiv"


def test_extract_iiif_label_language_map_sv():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_iiif_label({"sv": ["Svensk titel"]}) == "Svensk titel"


def test_extract_iiif_label_language_map_en():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_iiif_label({"en": ["English title"]}) == "English title"


def test_extract_iiif_label_language_map_none_key():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_iiif_label({"none": ["Untitled label"]}) == "Untitled label"


def test_extract_iiif_label_string():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_iiif_label("Plain string") == "Plain string"


def test_extract_iiif_label_default():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_iiif_label(None, "Fallback") == "Fallback"


def test_extract_manifest_identifier_manifest_url():
    http = HTTPClient()
    client = IIIFClient(http)
    url = "https://lbiiif.riksarkivet.se/arkis!R0001203/manifest"
    assert client._extract_manifest_identifier(url) == "arkis!R0001203"


def test_extract_manifest_identifier_plain_url():
    http = HTTPClient()
    client = IIIFClient(http)
    url = "https://lbiiif.riksarkivet.se/arkis/R0001203"
    assert client._extract_manifest_identifier(url) == "R0001203"


def test_extract_manifest_identifier_empty():
    http = HTTPClient()
    client = IIIFClient(http)
    assert client._extract_manifest_identifier("") == ""
