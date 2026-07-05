"""Tests for ra_mcp_pdf_mcp.models."""

import pytest

from ra_mcp_pdf_mcp.models import MatchedBlock, PageMatch, PdfViewerState, SearchResult


# ── PdfViewerState ───────────────────────────────────────────────────


def test_pdf_viewer_state_defaults():
    state = PdfViewerState()
    assert state.view_id == ""
    assert state.version == 0
    assert state.url == ""
    assert state.title == "Document"
    assert state.current_page == 1
    assert state.total_pages == 0
    assert state.go_to_page == -1
    assert state.search_term == ""
    assert state.request_fullscreen is False


def test_pdf_viewer_state_custom_fields():
    state = PdfViewerState(
        view_id="abc-123",
        version=3,
        url="https://example.com/doc.pdf",
        title="My Doc",
        current_page=5,
        total_pages=100,
    )
    assert state.view_id == "abc-123"
    assert state.version == 3
    assert state.current_page == 5
    assert state.total_pages == 100


# ── MatchedBlock ─────────────────────────────────────────────────────


def test_matched_block_to_structured():
    block = MatchedBlock(
        text="Trolldom i Norrland",
        bbox=[72, 100, 400, 130],
        block_type="Text",
        match_count=2,
    )
    result = block.to_structured()
    assert result == {
        "text": "Trolldom i Norrland",
        "bbox": [72, 100, 400, 130],
        "blockType": "Text",
        "matchCount": 2,
    }


# ── PageMatch ────────────────────────────────────────────────────────


def test_page_match_to_structured():
    block = MatchedBlock(text="text", bbox=[0, 0, 100, 50], block_type="Text", match_count=1)
    pm = PageMatch(
        page_index=0,
        page_num=1,
        match_count=1,
        page_bbox=[0, 0, 595, 842],
        blocks=[block],
    )
    result = pm.to_structured()
    assert result["pageIndex"] == 0
    assert result["pageNum"] == 1
    assert result["matchCount"] == 1
    assert result["pageBbox"] == [0, 0, 595, 842]
    assert len(result["blocks"]) == 1
    assert result["blocks"][0]["blockType"] == "Text"


# ── SearchResult ─────────────────────────────────────────────────────


def test_search_result_to_structured_empty():
    sr = SearchResult(page_matches=[], total_matches=0)
    result = sr.to_structured()
    assert result == {"pageMatches": [], "totalMatches": 0}


def test_search_result_to_structured_with_matches():
    block = MatchedBlock(text="match", bbox=[0, 0, 10, 10], block_type="Text", match_count=1)
    pm = PageMatch(page_index=2, page_num=3, match_count=1, page_bbox=[0, 0, 595, 842], blocks=[block])
    sr = SearchResult(page_matches=[pm], total_matches=1)
    result = sr.to_structured()
    assert result["totalMatches"] == 1
    assert len(result["pageMatches"]) == 1


@pytest.mark.parametrize(
    "total,term,expected_fragment",
    [
        pytest.param(1, "bok", "1 match for 'bok' across 1 page", id="singular"),
        pytest.param(5, "bok", "5 matches for 'bok' across", id="plural"),
    ],
)
def test_search_result_summary_grammar(total, term, expected_fragment):
    blocks = [MatchedBlock(text=f"contains {term} here", bbox=[0, 0, 10, 10], block_type="Text", match_count=total)]
    pm = PageMatch(page_index=0, page_num=1, match_count=total, page_bbox=[0, 0, 595, 842], blocks=blocks)
    sr = SearchResult(page_matches=[pm], total_matches=total)
    summary = sr.summary(term)
    assert expected_fragment in summary


def test_search_result_summary_truncates_at_10_snippets():
    blocks = [MatchedBlock(text=f"block {i}", bbox=[0, 0, 10, 10], block_type="Text", match_count=1) for i in range(15)]
    pms = [PageMatch(page_index=i, page_num=i + 1, match_count=1, page_bbox=[0, 0, 595, 842], blocks=[blocks[i]]) for i in range(15)]
    sr = SearchResult(page_matches=pms, total_matches=15)
    summary = sr.summary("term")
    snippet_lines = [line for line in summary.split("\n") if line.strip().startswith("p.")]
    assert len(snippet_lines) == 10
