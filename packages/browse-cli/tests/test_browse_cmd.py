"""Tests for browse CLI command."""

from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from ra_mcp_browse_cli.app import browse_app
from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_oai_pmh_lib import OAIPMHMetadata


REFERENCE_CODE = "SE/RA/310187/1"
MANIFEST_ID = "R0001203"

runner = CliRunner()


def _make_page_context(page_number: int = 1, text: str = "transcribed text") -> PageContext:
    return PageContext(
        page_number=page_number,
        page_id=str(page_number),
        reference_code=REFERENCE_CODE,
        full_text=text,
        alto_url=f"https://example.com/alto/{page_number}.xml",
        image_url=f"https://example.com/image/{page_number}.jpg",
        bildvisning_url=f"https://example.com/bild/{page_number}",
    )


def _make_browse_result(
    num_pages: int = 2,
    metadata: OAIPMHMetadata | None = None,
) -> BrowseResult:
    contexts = [_make_page_context(i + 1) for i in range(num_pages)]
    return BrowseResult(
        contexts=contexts,
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        manifest_id=MANIFEST_ID,
        oai_metadata=metadata or OAIPMHMetadata(identifier=REFERENCE_CODE, title="Test"),
    )


def _patch_browse(return_value: BrowseResult):
    return patch(
        "ra_mcp_browse_cli.browse_cmd.BrowseOperations",
        return_value=AsyncMock(browse_document=AsyncMock(return_value=return_value)),
    )


def test_browse_success():
    result_data = _make_browse_result(num_pages=2)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE])
    assert result.exit_code == 0
    assert "Browsing document" in result.output


def test_browse_with_pages_option():
    result_data = _make_browse_result(num_pages=3)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE, "--pages", "1-3"])
    assert result.exit_code == 0


def test_browse_with_page_option():
    result_data = _make_browse_result(num_pages=1)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE, "--page", "5"])
    assert result.exit_code == 0


def test_browse_page_takes_precedence_over_pages():
    result_data = _make_browse_result(num_pages=1)
    with _patch_browse(result_data) as mock_cls:
        runner.invoke(browse_app, [REFERENCE_CODE, "--pages", "1-10", "--page", "5"])
    mock_cls.return_value.browse_document.assert_called_once()
    call_kwargs = mock_cls.return_value.browse_document.call_args
    assert call_kwargs.kwargs.get("pages") == "5" or call_kwargs[1].get("pages") == "5"


def test_browse_with_search_term():
    result_data = _make_browse_result(num_pages=1)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE, "--search-term", "trolldom"])
    assert result.exit_code == 0


def test_browse_with_log_flag():
    result_data = _make_browse_result(num_pages=1)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE, "--log"])
    assert result.exit_code == 0
    assert "logging enabled" in result.output.lower()


def test_browse_with_show_links():
    result_data = _make_browse_result(num_pages=1)
    with _patch_browse(result_data):
        result = runner.invoke(browse_app, [REFERENCE_CODE, "--show-links"])
    assert result.exit_code == 0


def test_browse_no_pages_found():
    empty_result = BrowseResult(
        contexts=[],
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        oai_metadata=None,
    )
    with _patch_browse(empty_result):
        result = runner.invoke(browse_app, [REFERENCE_CODE])
    assert result.exit_code == 1
    assert "No pages found" in result.output


def test_browse_non_digitised_material():
    non_digitised = BrowseResult(
        contexts=[],
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        oai_metadata=OAIPMHMetadata(identifier=REFERENCE_CODE, title="Old doc"),
    )
    with _patch_browse(non_digitised):
        result = runner.invoke(browse_app, [REFERENCE_CODE])
    assert result.exit_code == 0


def test_browse_operation_error():
    with patch(
        "ra_mcp_browse_cli.browse_cmd.BrowseOperations",
        return_value=AsyncMock(browse_document=AsyncMock(side_effect=RuntimeError("API down"))),
    ):
        result = runner.invoke(browse_app, [REFERENCE_CODE])
    assert result.exit_code == 1
    assert "Browse failed" in result.output


def test_browse_no_args_shows_help():
    result = runner.invoke(browse_app, [])
    assert result.exit_code == 2
    assert "Usage" in result.output or "reference" in result.output.lower()
