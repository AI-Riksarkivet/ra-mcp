"""Tests for IIIFClient.fetch_manifest and related canvas parsing methods."""

import pytest

import httpx
import respx

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_iiif_lib.client import IIIFClient
from ra_mcp_iiif_lib.models import IIIFCanvas, IIIFManifestDetail


MANIFEST_URL = "https://lbiiif.riksarkivet.se/sdhk!85/manifest"

SAMPLE_MANIFEST = {
    "@context": "http://iiif.io/api/presentation/3/context.json",
    "id": MANIFEST_URL,
    "type": "Manifest",
    "label": {"sv": ["SDHK 85"]},
    "items": [
        {
            "type": "Canvas",
            "id": "https://lbiiif.riksarkivet.se/sdhk!85/canvas/p1",
            "label": {"none": ["1"]},
            "items": [
                {
                    "type": "AnnotationPage",
                    "items": [
                        {
                            "type": "Annotation",
                            "motivation": "painting",
                            "body": {
                                "type": "Image",
                                "id": "https://lbiiif.riksarkivet.se/sdhk!85/full/max/0/default.jpg",
                                "format": "image/jpeg",
                            },
                        }
                    ],
                }
            ],
        }
    ],
}


@respx.mock(assert_all_called=False)
async def test_fetch_manifest_returns_parsed_manifest(respx_mock):
    respx_mock.get(MANIFEST_URL).mock(return_value=httpx.Response(200, json=SAMPLE_MANIFEST))

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.fetch_manifest(MANIFEST_URL)
    finally:
        await http.aclose()

    assert result is not None
    assert isinstance(result, IIIFManifestDetail)
    assert result.id == MANIFEST_URL
    assert result.label == "SDHK 85"
    assert len(result.canvases) == 1


@respx.mock(assert_all_called=False)
async def test_fetch_manifest_canvas_has_correct_image_url(respx_mock):
    respx_mock.get(MANIFEST_URL).mock(return_value=httpx.Response(200, json=SAMPLE_MANIFEST))

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.fetch_manifest(MANIFEST_URL)
    finally:
        await http.aclose()

    assert result is not None
    canvas = result.canvases[0]
    assert canvas.id == "https://lbiiif.riksarkivet.se/sdhk!85/canvas/p1"
    assert canvas.label == "1"
    assert canvas.image_url == "https://lbiiif.riksarkivet.se/sdhk!85/full/max/0/default.jpg"


@respx.mock(assert_all_called=False)
async def test_fetch_manifest_returns_none_on_network_error(respx_mock):
    respx_mock.get(MANIFEST_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    http = HTTPClient()
    client = IIIFClient(http)
    try:
        result = await client.fetch_manifest(MANIFEST_URL)
    finally:
        await http.aclose()

    assert result is None


def test_parse_canvases_empty_items():
    http = HTTPClient()
    client = IIIFClient(http)
    result = client._parse_canvases([])
    assert result == []


def test_parse_canvases_skips_non_canvas_types():
    http = HTTPClient()
    client = IIIFClient(http)
    items = [
        {"type": "Manifest", "id": "https://example.com/manifest"},
        {"type": "AnnotationPage", "id": "https://example.com/page"},
    ]
    result = client._parse_canvases(items)
    assert result == []


def test_extract_painting_image_returns_empty_when_no_annotation():
    http = HTTPClient()
    client = IIIFClient(http)
    canvas = {"type": "Canvas", "id": "https://example.com/canvas/p1", "items": []}
    assert client._extract_painting_image(canvas) == ""


def test_extract_painting_image_returns_empty_when_wrong_motivation():
    http = HTTPClient()
    client = IIIFClient(http)
    canvas = {
        "type": "Canvas",
        "id": "https://example.com/canvas/p1",
        "items": [
            {
                "type": "AnnotationPage",
                "items": [
                    {
                        "type": "Annotation",
                        "motivation": "commenting",
                        "body": {"id": "https://example.com/image.jpg"},
                    }
                ],
            }
        ],
    }
    assert client._extract_painting_image(canvas) == ""


def test_extract_painting_image_returns_body_id():
    http = HTTPClient()
    client = IIIFClient(http)
    canvas = {
        "type": "Canvas",
        "id": "https://example.com/canvas/p1",
        "items": [
            {
                "type": "AnnotationPage",
                "items": [
                    {
                        "type": "Annotation",
                        "motivation": "painting",
                        "body": {"type": "Image", "id": "https://example.com/image.jpg"},
                    }
                ],
            }
        ],
    }
    assert client._extract_painting_image(canvas) == "https://example.com/image.jpg"


def test_parse_canvases_returns_correct_canvas_models():
    http = HTTPClient()
    client = IIIFClient(http)
    items = SAMPLE_MANIFEST["items"]
    result = client._parse_canvases(items)

    assert len(result) == 1
    assert isinstance(result[0], IIIFCanvas)
    assert result[0].id == "https://lbiiif.riksarkivet.se/sdhk!85/canvas/p1"
    assert result[0].image_url == "https://lbiiif.riksarkivet.se/sdhk!85/full/max/0/default.jpg"
