"""Tests for HTTPClient — retry logic, get_json, get_xml, get_content, helpers."""

import json
import logging

import httpx
import pytest
import respx

from ra_mcp_common.http_client import (
    HTTPClient,
    _DEFAULT_BACKOFF_BASE,
    _DEFAULT_MAX_RETRIES,
    _RETRYABLE_STATUS_CODES,
    default_http_client,
    get_http_client,
)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_default_user_agent():
    client = HTTPClient()
    assert client.user_agent.startswith("ra-mcp/")


def test_custom_user_agent():
    client = HTTPClient(user_agent="test-agent/1.0")
    assert client.user_agent == "test-agent/1.0"


def test_default_retry_settings():
    client = HTTPClient()
    assert client.max_retries == _DEFAULT_MAX_RETRIES
    assert client.backoff_base == _DEFAULT_BACKOFF_BASE


def test_custom_retry_settings():
    client = HTTPClient(max_retries=5, backoff_base=1.0)
    assert client.max_retries == 5
    assert client.backoff_base == 1.0


# ---------------------------------------------------------------------------
# get_json — success
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_json_success(respx_mock):
    payload = {"results": [1, 2, 3], "total": 3}
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json=payload)
    )

    client = HTTPClient()
    try:
        result = await client.get_json("https://api.example.com/data")
    finally:
        await client.aclose()

    assert result == payload


@respx.mock(assert_all_called=False)
async def test_get_json_with_params(respx_mock):
    respx_mock.get("https://api.example.com/search").mock(
        return_value=httpx.Response(200, json={"q": "test"})
    )

    client = HTTPClient()
    try:
        result = await client.get_json(
            "https://api.example.com/search", params={"q": "test", "limit": 10}
        )
    finally:
        await client.aclose()

    assert result == {"q": "test"}
    call = respx_mock.calls[0]
    assert "q=test" in str(call.request.url)
    assert "limit=10" in str(call.request.url)


@respx.mock(assert_all_called=False)
async def test_get_json_with_custom_headers(respx_mock):
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={})
    )

    client = HTTPClient()
    try:
        await client.get_json(
            "https://api.example.com/data", headers={"X-Custom": "value"}
        )
    finally:
        await client.aclose()

    call = respx_mock.calls[0]
    assert call.request.headers["X-Custom"] == "value"
    assert call.request.headers["Accept"] == "application/json"


# ---------------------------------------------------------------------------
# get_json — error paths
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_json_timeout_raises(respx_mock):
    respx_mock.get("https://api.example.com/slow").mock(
        side_effect=httpx.ReadTimeout("read timed out")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(TimeoutError, match="Request timeout"):
            await client.get_json("https://api.example.com/slow", timeout=1)
    finally:
        await client.aclose()


@respx.mock(assert_all_called=False)
async def test_get_json_connect_error_raises(respx_mock):
    respx_mock.get("https://api.example.com/down").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(httpx.ConnectError):
            await client.get_json("https://api.example.com/down")
    finally:
        await client.aclose()


@respx.mock(assert_all_called=False)
async def test_get_json_invalid_json_raises(respx_mock):
    respx_mock.get("https://api.example.com/bad").mock(
        return_value=httpx.Response(200, content=b"not json")
    )

    client = HTTPClient()
    try:
        with pytest.raises(json.JSONDecodeError):
            await client.get_json("https://api.example.com/bad")
    finally:
        await client.aclose()


@respx.mock(assert_all_called=False)
async def test_get_json_non_200_raises(respx_mock):
    respx_mock.get("https://api.example.com/err").mock(
        return_value=httpx.Response(403, text="Forbidden")
    )

    client = HTTPClient()
    try:
        with pytest.raises(Exception, match="HTTP 403"):
            await client.get_json("https://api.example.com/err")
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# get_json — timeout env override
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_json_timeout_env_override(respx_mock, monkeypatch):
    monkeypatch.setenv("RA_MCP_TIMEOUT", "120")
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    client = HTTPClient()
    try:
        result = await client.get_json("https://api.example.com/data", timeout=5)
    finally:
        await client.aclose()

    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# get_xml — success
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_xml_success(respx_mock):
    xml_body = b"<root><item>1</item></root>"
    respx_mock.get("https://api.example.com/xml").mock(
        return_value=httpx.Response(200, content=xml_body)
    )

    client = HTTPClient()
    try:
        result = await client.get_xml("https://api.example.com/xml")
    finally:
        await client.aclose()

    assert result == xml_body


@respx.mock(assert_all_called=False)
async def test_get_xml_with_params_and_headers(respx_mock):
    respx_mock.get("https://api.example.com/xml").mock(
        return_value=httpx.Response(200, content=b"<ok/>")
    )

    client = HTTPClient()
    try:
        await client.get_xml(
            "https://api.example.com/xml",
            params={"id": "123"},
            headers={"X-Key": "val"},
        )
    finally:
        await client.aclose()

    call = respx_mock.calls[0]
    assert "id=123" in str(call.request.url)
    assert call.request.headers["X-Key"] == "val"
    assert "xml" in call.request.headers["Accept"]


# ---------------------------------------------------------------------------
# get_xml — error paths
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_xml_timeout_raises(respx_mock):
    respx_mock.get("https://api.example.com/xml").mock(
        side_effect=httpx.ReadTimeout("read timed out")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(TimeoutError, match="Request timeout"):
            await client.get_xml("https://api.example.com/xml")
    finally:
        await client.aclose()


@respx.mock(assert_all_called=False)
async def test_get_xml_connect_error_raises(respx_mock):
    respx_mock.get("https://api.example.com/xml").mock(
        side_effect=httpx.ConnectError("refused")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(httpx.ConnectError):
            await client.get_xml("https://api.example.com/xml")
    finally:
        await client.aclose()


@respx.mock(assert_all_called=False)
async def test_get_xml_non_200_raises(respx_mock):
    respx_mock.get("https://api.example.com/xml").mock(
        return_value=httpx.Response(500, text="fail")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(Exception, match="HTTP 500"):
            await client.get_xml("https://api.example.com/xml")
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# get_content — success
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_content_success(respx_mock):
    body = b"\x89PNG\r\n\x1a\nbinary data"
    respx_mock.get("https://api.example.com/image").mock(
        return_value=httpx.Response(200, content=body)
    )

    client = HTTPClient()
    try:
        result = await client.get_content("https://api.example.com/image")
    finally:
        await client.aclose()

    assert result == body


@respx.mock(assert_all_called=False)
async def test_get_content_returns_none_on_404(respx_mock):
    respx_mock.get("https://api.example.com/missing").mock(
        return_value=httpx.Response(404)
    )

    client = HTTPClient()
    try:
        result = await client.get_content("https://api.example.com/missing")
    finally:
        await client.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_get_content_returns_none_on_non_200(respx_mock):
    respx_mock.get("https://api.example.com/err").mock(
        return_value=httpx.Response(403)
    )

    client = HTTPClient()
    try:
        result = await client.get_content("https://api.example.com/err")
    finally:
        await client.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_get_content_returns_none_on_timeout(respx_mock):
    respx_mock.get("https://api.example.com/slow").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        result = await client.get_content("https://api.example.com/slow")
    finally:
        await client.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_get_content_returns_none_on_connect_error(respx_mock):
    respx_mock.get("https://api.example.com/down").mock(
        side_effect=httpx.ConnectError("refused")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        result = await client.get_content("https://api.example.com/down")
    finally:
        await client.aclose()

    assert result is None


@respx.mock(assert_all_called=False)
async def test_get_content_with_headers(respx_mock):
    respx_mock.get("https://api.example.com/image").mock(
        return_value=httpx.Response(200, content=b"OK")
    )

    client = HTTPClient()
    try:
        await client.get_content(
            "https://api.example.com/image", headers={"Authorization": "Bearer token"}
        )
    finally:
        await client.aclose()

    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer token"


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status_code",
    [
        pytest.param(429, id="too-many-requests"),
        pytest.param(500, id="internal-server-error"),
        pytest.param(502, id="bad-gateway"),
        pytest.param(503, id="service-unavailable"),
        pytest.param(504, id="gateway-timeout"),
    ],
)
@respx.mock(assert_all_called=False)
async def test_retry_on_retryable_status_codes(respx_mock, status_code):
    route = respx_mock.get("https://api.example.com/flaky")
    route.side_effect = [
        httpx.Response(status_code),
        httpx.Response(200, json={"ok": True}),
    ]

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        result = await client.get_json("https://api.example.com/flaky")
    finally:
        await client.aclose()

    assert result == {"ok": True}
    assert len(respx_mock.calls) == 2


@respx.mock(assert_all_called=False)
async def test_retry_exhausted_raises(respx_mock):
    respx_mock.get("https://api.example.com/down").mock(
        return_value=httpx.Response(503)
    )

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        with pytest.raises(Exception, match="HTTP 503"):
            await client.get_json("https://api.example.com/down")
    finally:
        await client.aclose()

    assert len(respx_mock.calls) == 2


@respx.mock(assert_all_called=False)
async def test_retry_on_timeout_exception(respx_mock):
    route = respx_mock.get("https://api.example.com/slow")
    route.side_effect = [
        httpx.ReadTimeout("timed out"),
        httpx.Response(200, json={"recovered": True}),
    ]

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        result = await client.get_json("https://api.example.com/slow")
    finally:
        await client.aclose()

    assert result == {"recovered": True}


@respx.mock(assert_all_called=False)
async def test_retry_on_connect_error(respx_mock):
    route = respx_mock.get("https://api.example.com/flaky")
    route.side_effect = [
        httpx.ConnectError("refused"),
        httpx.Response(200, json={"ok": True}),
    ]

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        result = await client.get_json("https://api.example.com/flaky")
    finally:
        await client.aclose()

    assert result == {"ok": True}


@respx.mock(assert_all_called=False)
async def test_no_retry_on_non_retryable_status(respx_mock):
    respx_mock.get("https://api.example.com/bad").mock(
        return_value=httpx.Response(400, text="Bad Request")
    )

    client = HTTPClient(max_retries=3, backoff_base=0.0)
    try:
        with pytest.raises(Exception, match="HTTP 400"):
            await client.get_json("https://api.example.com/bad")
    finally:
        await client.aclose()

    assert len(respx_mock.calls) == 1


def test_retryable_status_codes_set():
    assert _RETRYABLE_STATUS_CODES == {429, 500, 502, 503, 504}


# ---------------------------------------------------------------------------
# aclose
# ---------------------------------------------------------------------------


async def test_aclose():
    client = HTTPClient()
    await client.aclose()
    assert client._client.is_closed


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def test_default_http_client_is_singleton():
    assert default_http_client is get_http_client()


def test_get_http_client_returns_default():
    client = get_http_client(enable_logging=False)
    assert client is default_http_client


def test_get_http_client_enable_logging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = get_http_client(enable_logging=True)
    assert client is default_http_client

    root = logging.getLogger()
    assert any(
        isinstance(h, logging.FileHandler) and h.baseFilename.endswith("ra_mcp_api.log")
        for h in root.handlers
    )

    # Second call should not duplicate the handler
    count_before = sum(
        1 for h in root.handlers
        if isinstance(h, logging.FileHandler) and h.baseFilename.endswith("ra_mcp_api.log")
    )
    get_http_client(enable_logging=True)
    count_after = sum(
        1 for h in root.handlers
        if isinstance(h, logging.FileHandler) and h.baseFilename.endswith("ra_mcp_api.log")
    )
    assert count_after == count_before

    # Cleanup: remove the file handler so it doesn't leak into other tests
    root.handlers = [
        h for h in root.handlers
        if not (isinstance(h, logging.FileHandler) and h.baseFilename.endswith("ra_mcp_api.log"))
    ]


# ---------------------------------------------------------------------------
# _execute_with_retry — HTTPStatusError paths
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_retry_on_http_status_error_retryable(respx_mock):
    """HTTPStatusError with retryable status retries and recovers."""
    route = respx_mock.get("https://api.example.com/flaky")
    route.side_effect = [
        httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "https://api.example.com/flaky"),
            response=httpx.Response(503),
        ),
        httpx.Response(200, json={"recovered": True}),
    ]

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        result = await client.get_json("https://api.example.com/flaky")
    finally:
        await client.aclose()

    assert result == {"recovered": True}
    assert len(respx_mock.calls) == 2


@respx.mock(assert_all_called=False)
async def test_retry_on_http_status_error_non_retryable(respx_mock):
    """HTTPStatusError with non-retryable status raises immediately."""
    respx_mock.get("https://api.example.com/bad").mock(
        side_effect=httpx.HTTPStatusError(
            "Forbidden",
            request=httpx.Request("GET", "https://api.example.com/bad"),
            response=httpx.Response(403),
        )
    )

    client = HTTPClient(max_retries=3, backoff_base=0.0)
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_json("https://api.example.com/bad")
    finally:
        await client.aclose()

    assert len(respx_mock.calls) == 1


@respx.mock(assert_all_called=False)
async def test_retry_http_status_error_exhausted(respx_mock):
    """HTTPStatusError retries exhausted raises the last error."""
    respx_mock.get("https://api.example.com/flaky").mock(
        side_effect=httpx.HTTPStatusError(
            "Bad Gateway",
            request=httpx.Request("GET", "https://api.example.com/flaky"),
            response=httpx.Response(502),
        )
    )

    client = HTTPClient(max_retries=2, backoff_base=0.0)
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_json("https://api.example.com/flaky")
    finally:
        await client.aclose()

    assert len(respx_mock.calls) == 2


# ---------------------------------------------------------------------------
# get_json — HTTPStatusError
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_json_http_status_error(respx_mock):
    """get_json re-raises HTTPStatusError from _execute_with_retry."""
    respx_mock.get("https://api.example.com/err").mock(
        side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("GET", "https://api.example.com/err"),
            response=httpx.Response(404, text="not found"),
        )
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_json("https://api.example.com/err")
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# get_xml — HTTPStatusError
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_xml_http_status_error(respx_mock):
    """get_xml re-raises HTTPStatusError from _execute_with_retry."""
    respx_mock.get("https://api.example.com/xml").mock(
        side_effect=httpx.HTTPStatusError(
            "Forbidden",
            request=httpx.Request("GET", "https://api.example.com/xml"),
            response=httpx.Response(403, text="forbidden"),
        )
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_xml("https://api.example.com/xml")
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# get_content — generic exception
# ---------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
async def test_get_content_returns_none_on_generic_exception(respx_mock):
    """get_content catches generic exceptions and returns None."""
    respx_mock.get("https://api.example.com/crash").mock(
        side_effect=RuntimeError("unexpected")
    )

    client = HTTPClient(max_retries=1, backoff_base=0.0)
    try:
        result = await client.get_content("https://api.example.com/crash")
    finally:
        await client.aclose()

    assert result is None
