"""Tests for ALTO XML client with mocked HTTP."""

import httpx
import respx

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_xml import ALTOClient, TextLayer


ALTO_URL = "https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml"


@respx.mock(assert_all_called=False)
async def test_fetch_content_success(respx_mock, alto_sample_xml):
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(200, content=alto_sample_xml))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert isinstance(result, TextLayer)
    # Real data from R0001203 page 7 (htrflow transcription)
    assert "högstbonde" in result.full_text
    assert "hans" in result.full_text
    assert "Kongl." in result.full_text
    assert "Remissorial," in result.full_text
    assert "Fsenatens" in result.full_text


@respx.mock(assert_all_called=False)
async def test_fetch_content_blank_page(respx_mock, alto_blank_xml):
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(200, content=alto_blank_xml))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert isinstance(result, TextLayer)
    assert result.full_text == ""


@respx.mock(assert_all_called=False)
async def test_fetch_content_not_found(respx_mock):
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(404))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_fetch_content_parse_error(respx_mock):
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(200, content=b"<not valid xml"))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_fetch_content_alto_v2_namespace(respx_mock):
    """ALTO with v2 namespace should also be parsed."""
    alto_v2 = b"""<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v2#">
  <Layout>
    <Page>
      <PrintSpace>
        <TextBlock>
          <TextLine>
            <String CONTENT="Hej" HPOS="0" VPOS="0" WIDTH="100" HEIGHT="50"/>
            <String CONTENT="v&#228;rlden" HPOS="110" VPOS="0" WIDTH="200" HEIGHT="50"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>"""
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(200, content=alto_v2))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert result.full_text == "Hej världen"


@respx.mock(assert_all_called=False)
async def test_fetch_content_no_namespace(respx_mock):
    """ALTO without namespace should still be parsed."""
    alto_no_ns = b"""<?xml version="1.0" encoding="UTF-8"?>
<alto>
  <Layout>
    <Page>
      <PrintSpace>
        <TextBlock>
          <TextLine>
            <String CONTENT="Test" HPOS="0" VPOS="0" WIDTH="100" HEIGHT="50"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>"""
    respx_mock.get(ALTO_URL).mock(return_value=httpx.Response(200, content=alto_no_ns))

    http = HTTPClient()
    client = ALTOClient(http)
    try:
        result = await client.fetch_content(ALTO_URL)
    finally:
        await http.aclose()

    assert result.full_text == "Test"
