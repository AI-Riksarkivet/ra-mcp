"""Tests for OAI-PMH client with mocked HTTP."""

import httpx
import respx

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_oai_pmh_lib import OAIPMHClient, OAIPMHMetadata
from ra_mcp_oai_pmh_lib.config import OAI_BASE_URL


IDENTIFIER = "SE/RA/310187/1"


@respx.mock(assert_all_called=False)
async def test_get_metadata_success(respx_mock, oai_pmh_xml):
    respx_mock.get(OAI_BASE_URL).mock(return_value=httpx.Response(200, content=oai_pmh_xml))

    http = HTTPClient()
    client = OAIPMHClient(http)
    try:
        result = await client.get_metadata(IDENTIFIER)
    finally:
        await http.aclose()

    assert result is not None
    assert result.identifier == IDENTIFIER
    # Real data from OAI-PMH API for SE/RA/310187/1
    assert result.title == "1676--1677"
    assert result.unitid == "SE/RA/310187/1"
    assert result.unitdate == "1676--1677"
    assert result.description == "Protokoll 30 juni 1676 - 3 juli 1677. Band"
    assert result.nad_link == "https://sok.riksarkivet.se/bildvisning/R0001203?partner=ape"
    assert result.iiif_manifest == "https://lbiiif.riksarkivet.se/arkis!R0001203/manifest"
    assert result.iiif_image == "https://lbiiif.riksarkivet.se/v2/arkis!R0001203_00319/full/full/0/default.jpg"
    assert result.datestamp == "2025-03-27T16:21:42.223Z"


@respx.mock(assert_all_called=False)
async def test_get_metadata_error(respx_mock):
    respx_mock.get(OAI_BASE_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    http = HTTPClient()
    client = OAIPMHClient(http)
    try:
        result = await client.get_metadata(IDENTIFIER)
    finally:
        await http.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_oai_error_response(respx_mock):
    error_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>2024-01-15T12:00:00Z</responseDate>
  <error code="idDoesNotExist">No matching identifier</error>
</OAI-PMH>"""
    respx_mock.get(OAI_BASE_URL).mock(return_value=httpx.Response(200, content=error_xml))

    http = HTTPClient()
    client = OAIPMHClient(http)
    try:
        result = await client.get_metadata(IDENTIFIER)
    finally:
        await http.aclose()

    # OAI error should be caught, returning None
    assert result is None


def test_manifest_id_from_metadata():
    metadata = OAIPMHMetadata(
        identifier=IDENTIFIER,
        nad_link="https://sok.riksarkivet.se/bildvisning/R0001203?partner=ape",
    )
    http = HTTPClient()
    client = OAIPMHClient(http)
    assert client.manifest_id_from_metadata(metadata) == "R0001203"


def test_manifest_id_from_metadata_none():
    http = HTTPClient()
    client = OAIPMHClient(http)
    assert client.manifest_id_from_metadata(None) is None


def test_manifest_id_from_metadata_no_nad_link():
    metadata = OAIPMHMetadata(identifier=IDENTIFIER, nad_link=None)
    http = HTTPClient()
    client = OAIPMHClient(http)
    assert client.manifest_id_from_metadata(metadata) is None


def test_manifest_id_from_metadata_trailing_slash():
    metadata = OAIPMHMetadata(
        identifier=IDENTIFIER,
        nad_link="https://sok.riksarkivet.se/bildvisning/R0001203/",
    )
    http = HTTPClient()
    client = OAIPMHClient(http)
    assert client.manifest_id_from_metadata(metadata) == "R0001203"


@respx.mock(assert_all_called=False)
async def test_extract_manifest_id(respx_mock, oai_pmh_xml):
    respx_mock.get(OAI_BASE_URL).mock(return_value=httpx.Response(200, content=oai_pmh_xml))

    http = HTTPClient()
    client = OAIPMHClient(http)
    try:
        result = await client.extract_manifest_id(IDENTIFIER)
    finally:
        await http.aclose()

    assert result == "R0001203"
