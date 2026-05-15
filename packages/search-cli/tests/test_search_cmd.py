"""Tests for search CLI command."""

from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from ra_mcp_search_cli.app import search_app
from ra_mcp_search_lib.models import (
    Metadata,
    PageInfo,
    RecordsResponse,
    SearchRecord,
    SearchResult,
    Snippet,
    TranscribedText,
)


runner = CliRunner()


def _make_search_result(
    keyword: str = "trolldom",
    num_records: int = 2,
    total_hits: int = 10,
    offset: int = 0,
    limit: int = 50,
) -> SearchResult:
    items = [
        SearchRecord(
            id=f"SE/RA/TEST/{i}",
            objectType="Record",
            type="Volume",
            caption=f"Test Record {i}",
            metadata=Metadata(referenceCode=f"SE/RA/TEST/{i}"),
            transcribedText=TranscribedText(
                numTotal=3,
                snippets=[
                    Snippet(text=f"snippet with {keyword}", score=0.9, pages=[PageInfo(id="_00001")])
                ],
            ),
        )
        for i in range(num_records)
    ]
    response = RecordsResponse(totalHits=total_hits, items=items, hits=num_records, offset=offset)
    return SearchResult(response=response, transcribed_text=keyword, limit=limit, offset=offset)


def _patch_search(return_value: SearchResult):
    return patch(
        "ra_mcp_search_cli.search_cmd.SearchOperations",
        return_value=AsyncMock(search=AsyncMock(return_value=return_value)),
    )


def test_search_success():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom"])
    assert result.exit_code == 0


def test_search_with_limit():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom", "--limit", "100"])
    assert result.exit_code == 0


def test_search_with_max_display():
    result_data = _make_search_result(num_records=5)
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom", "--max-display", "2"])
    assert result.exit_code == 0


def test_search_with_max_hits_per_vol():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom", "--max-hits-per-vol", "1"])
    assert result.exit_code == 0


def test_search_text_mode():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom", "--text"])
    assert result.exit_code == 0


def test_search_include_all_materials_switches_to_text():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["Stockholm", "--include-all-materials"])
    assert result.exit_code == 0
    assert "switching to --text" in result.output.lower() or "automatically switching" in result.output.lower()


def test_search_with_log_flag():
    result_data = _make_search_result()
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["trolldom", "--log"])
    assert result.exit_code == 0
    assert "logging enabled" in result.output.lower()


def test_search_no_results():
    result_data = _make_search_result(num_records=0, total_hits=0)
    with _patch_search(result_data):
        result = runner.invoke(search_app, ["nonexistent"])
    assert result.exit_code == 0


def test_search_operation_error():
    with patch(
        "ra_mcp_search_cli.search_cmd.SearchOperations",
        return_value=AsyncMock(search=AsyncMock(side_effect=RuntimeError("API down"))),
    ):
        result = runner.invoke(search_app, ["trolldom"])
    assert result.exit_code == 1
    assert "Search failed" in result.output


def test_search_no_args_shows_help():
    result = runner.invoke(search_app, [])
    assert result.exit_code == 2
    assert "Usage" in result.output or "keyword" in result.output.lower()


def test_search_help_flag():
    result = runner.invoke(search_app, ["--help"])
    assert result.exit_code == 0
    assert "keyword" in result.output.lower() or "search" in result.output.lower()
