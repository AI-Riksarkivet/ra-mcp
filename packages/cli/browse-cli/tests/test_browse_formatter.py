"""Tests for browse-cli RichConsoleFormatter."""

import pytest
from rich.console import Console
from rich.panel import Panel

from ra_mcp_browse_cli.formatter import RichConsoleFormatter
from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_oai_pmh_lib import OAIPMHMetadata


REFERENCE_CODE = "SE/RA/310187/1"
MANIFEST_ID = "R0001203"


def _make_formatter() -> RichConsoleFormatter:
    return RichConsoleFormatter(Console(force_terminal=True, width=120))


def _make_page_context(
    page_number: int = 1,
    text: str = "some transcribed text",
    ref_code: str = REFERENCE_CODE,
) -> PageContext:
    return PageContext(
        page_number=page_number,
        page_id=str(page_number),
        reference_code=ref_code,
        full_text=text,
        alto_url=f"https://sok.riksarkivet.se/dokument/alto/{MANIFEST_ID}_{page_number:05d}.xml",
        image_url=f"https://lbiiif.riksarkivet.se/arkis!{MANIFEST_ID}_{page_number:05d}/full/max/0/default.jpg",
        bildvisning_url=f"https://sok.riksarkivet.se/bildvisning/{MANIFEST_ID}_{page_number:05d}",
    )


def _make_metadata(**overrides) -> OAIPMHMetadata:
    defaults = {
        "identifier": REFERENCE_CODE,
        "title": "Test Document",
        "unitdate": "1700-1800",
        "repository": "Riksarkivet",
    }
    defaults.update(overrides)
    return OAIPMHMetadata(**defaults)


def _make_browse_result(
    num_pages: int = 2,
    metadata: OAIPMHMetadata | None = None,
    contexts: list[PageContext] | None = None,
) -> BrowseResult:
    if contexts is None:
        contexts = [_make_page_context(i + 1) for i in range(num_pages)]
    return BrowseResult(
        contexts=contexts,
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        manifest_id=MANIFEST_ID,
        oai_metadata=metadata,
    )


# ── highlight_search_keyword ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,keyword,expected_fragment",
    [
        pytest.param(
            "found **trolldom** here",
            "trolldom",
            "[bold yellow underline]trolldom[/bold yellow underline]",
            id="api-markers-converted",
        ),
        pytest.param(
            "text with Trolldom inside",
            "trolldom",
            "[bold yellow underline]Trolldom[/bold yellow underline]",
            id="keyword-case-insensitive",
        ),
        pytest.param(
            "no markers here",
            "",
            "no markers here",
            id="empty-keyword-unchanged",
        ),
        pytest.param(
            "no match at all",
            "xyz",
            "no match at all",
            id="keyword-not-found",
        ),
    ],
)
def test_highlight_search_keyword(text, keyword, expected_fragment):
    result = _make_formatter().highlight_search_keyword(text, keyword)
    assert expected_fragment in result


def test_highlight_api_markers_take_precedence():
    result = _make_formatter().highlight_search_keyword("**word** and more", "more")
    assert "[bold yellow underline]word[/bold yellow underline]" in result
    assert "[bold yellow underline]more[/bold yellow underline]" not in result


# ── format_browse_results ───────────────────────────────────────────────


def test_format_browse_results_with_pages():
    browse = _make_browse_result(num_pages=3, metadata=_make_metadata())
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)
    assert any("Successfully loaded 3 pages" in str(item) for item in output if isinstance(item, str))


def test_format_browse_results_no_success_message():
    browse = _make_browse_result(num_pages=1)
    output = _make_formatter().format_browse_results(browse, show_success_message=False)
    assert not any("Successfully loaded" in str(item) for item in output if isinstance(item, str))


def test_format_browse_results_with_highlight():
    browse = _make_browse_result(
        contexts=[_make_page_context(1, "text with keyword here")],
        metadata=_make_metadata(),
    )
    output = _make_formatter().format_browse_results(browse, highlight_term="keyword")
    assert any(isinstance(item, Panel) for item in output)


def test_format_browse_results_with_show_links():
    browse = _make_browse_result(num_pages=1, metadata=_make_metadata())
    output = _make_formatter().format_browse_results(browse, show_links=True)
    assert any(isinstance(item, Panel) for item in output)


def test_format_browse_results_groups_by_reference_code():
    ctx_a1 = _make_page_context(1, ref_code="SE/RA/A")
    ctx_a2 = _make_page_context(2, ref_code="SE/RA/A")
    ctx_b1 = _make_page_context(1, ref_code="SE/RA/B")
    browse = _make_browse_result(contexts=[ctx_a1, ctx_a2, ctx_b1])
    output = _make_formatter().format_browse_results(browse)
    panels = [item for item in output if isinstance(item, Panel)]
    assert len(panels) == 2


def test_format_browse_results_sorts_pages():
    ctx3 = _make_page_context(3)
    ctx1 = _make_page_context(1)
    ctx2 = _make_page_context(2)
    browse = _make_browse_result(contexts=[ctx3, ctx1, ctx2])
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)


def test_format_browse_results_empty_page_text():
    ctx = _make_page_context(1, text="")
    browse = _make_browse_result(contexts=[ctx])
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)


# ── _format_non_digitised_panel ──────────────────────────────────────────


def test_format_non_digitised_panel():
    metadata = _make_metadata(
        nad_link="https://sok.riksarkivet.se/bildvisning/R0001203",
        description="A detailed description",
    )
    browse = BrowseResult(
        contexts=[],
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        oai_metadata=metadata,
    )
    output = _make_formatter().format_browse_results(browse)
    assert any("not digitised" in str(item).lower() for item in output)
    assert any(isinstance(item, Panel) for item in output)


def test_format_non_digitised_panel_truncates_long_description():
    metadata = _make_metadata(description="x" * 500)
    browse = BrowseResult(
        contexts=[],
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        oai_metadata=metadata,
    )
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)


def test_format_non_digitised_no_metadata():
    browse = BrowseResult(
        contexts=[],
        reference_code=REFERENCE_CODE,
        pages_requested="1-20",
        oai_metadata=None,
    )
    output = _make_formatter().format_browse_results(browse)
    assert output == []


# ── _format_group_metadata ──────────────────────────────────────────────


def test_format_group_metadata_included_in_browse():
    metadata = _make_metadata(
        unitid="VOL-1",
        description="Short desc",
        nad_link="https://example.com/nad",
    )
    browse = _make_browse_result(num_pages=1, metadata=metadata)
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)


def test_format_browse_results_no_metadata():
    browse = _make_browse_result(num_pages=1, metadata=None)
    output = _make_formatter().format_browse_results(browse)
    assert any(isinstance(item, Panel) for item in output)
