"""Tests for result_list module: ResultList and PageList static/pure helpers."""

import pytest
from rich.text import Text

from ra_mcp_search_lib.models import GenericReference

from ra_mcp_tui.widgets.result_list import ResultList, _ArchiveNode, _SnippetNode

from conftest import make_page_context, make_search_record


# ---------------------------------------------------------------------------
# ResultList._styled_snippet
# ---------------------------------------------------------------------------


def test_styled_snippet_plain_text():
    result = ResultList._styled_snippet("some plain text", 7)
    assert isinstance(result, Text)
    assert result.plain.startswith("p.7: ")
    assert "some plain text" in result.plain


def test_styled_snippet_em_highlighted():
    result = ResultList._styled_snippet("found <em>trolldom</em> here", 12)
    assert "trolldom" in result.plain
    assert "<em>" not in result.plain


@pytest.mark.parametrize(
    "raw,page,expected_prefix",
    [
        pytest.param("text", 0, "p.0: ", id="page-zero"),
        pytest.param("text", 999, "p.999: ", id="large-page"),
        pytest.param("", 1, "p.1: ", id="empty-text"),
    ],
)
def test_styled_snippet_prefix(raw, page, expected_prefix):
    result = ResultList._styled_snippet(raw, page)
    assert result.plain.startswith(expected_prefix)


def test_styled_snippet_strips_newlines():
    result = ResultList._styled_snippet("line one\nline two\nline three", 1)
    assert "\n" not in result.plain


def test_styled_snippet_multiple_em():
    result = ResultList._styled_snippet("<em>first</em> and <em>second</em>", 1)
    assert "first" in result.plain
    assert "second" in result.plain
    assert "<em>" not in result.plain


def test_styled_snippet_truncates_long_text():
    long_text = "a" * 300
    result = ResultList._styled_snippet(long_text, 1)
    assert len(result.plain) <= 200 + 10  # prefix + ellipsis


# ---------------------------------------------------------------------------
# ResultList._truncate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,max_len,expected",
    [
        pytest.param("short", 10, "short", id="under-limit"),
        pytest.param("exactly10!", 10, "exactly10!", id="at-limit"),
        pytest.param("this is too long", 10, "this is t…", id="over-limit"),
        pytest.param("", 5, "", id="empty"),
        pytest.param("a", 1, "a", id="single-char-at-limit"),
        pytest.param("ab", 1, "…", id="over-by-one"),
    ],
)
def test_truncate(text, max_len, expected):
    assert ResultList._truncate(text, max_len) == expected


# ---------------------------------------------------------------------------
# ResultList._node_metadata
# ---------------------------------------------------------------------------


def test_node_metadata_depth_0_returns_none():
    record = make_search_record()
    assert ResultList._node_metadata(record, 0) is None


def test_node_metadata_depth_1_archival_institution():
    record = make_search_record(
        archival_institution=[GenericReference(caption="Riksarkivet", uri="https://ra.se")],
    )
    node = ResultList._node_metadata(record, 1)
    assert isinstance(node, _ArchiveNode)
    assert node.caption == "Riksarkivet"
    assert node.uri == "https://ra.se"


def test_node_metadata_depth_2_hierarchy():
    record = make_search_record(
        hierarchy=[GenericReference(caption="Svea hovrätt", uri="https://example.com/svea")],
    )
    node = ResultList._node_metadata(record, 2)
    assert isinstance(node, _ArchiveNode)
    assert node.caption == "Svea hovrätt"


def test_node_metadata_depth_2_fallback_provenance():
    record = make_search_record(
        hierarchy=None,
        provenance=[GenericReference(caption="Provenance caption", uri="https://prov.se")],
    )
    node = ResultList._node_metadata(record, 2)
    assert isinstance(node, _ArchiveNode)
    assert node.caption == "Provenance caption"


def test_node_metadata_depth_3_hierarchy_index():
    record = make_search_record(
        hierarchy=[
            GenericReference(caption="level-0"),
            GenericReference(caption="level-1"),
        ],
    )
    node = ResultList._node_metadata(record, 3)
    assert isinstance(node, _ArchiveNode)
    assert node.caption == "level-1"


def test_node_metadata_depth_beyond_hierarchy_returns_none():
    record = make_search_record(hierarchy=[GenericReference(caption="only-one")])
    assert ResultList._node_metadata(record, 4) is None


def test_node_metadata_depth_1_no_institution_returns_none():
    record = make_search_record(archival_institution=None)
    assert ResultList._node_metadata(record, 1) is None


# ---------------------------------------------------------------------------
# ResultList._ref_from_node / _link_from_node / _note_from_node
# ---------------------------------------------------------------------------


class _FakeNode:
    """Minimal stand-in for a TreeNode with .data."""

    def __init__(self, data):
        self.data = data


def test_ref_from_node_search_record():
    record = make_search_record(reference_code="SE/RA/123")
    assert ResultList._ref_from_node(_FakeNode(record)) == "SE/RA/123"


def test_ref_from_node_snippet_node():
    record = make_search_record(reference_code="SE/RA/456")
    node = _SnippetNode(record=record, page_number=7, text="hit")
    assert ResultList._ref_from_node(_FakeNode(node)) == "SE/RA/456"


def test_ref_from_node_archive_node():
    assert ResultList._ref_from_node(_FakeNode(_ArchiveNode(uri="u", caption="c"))) is None


def test_ref_from_node_none_data():
    assert ResultList._ref_from_node(_FakeNode(None)) is None


def test_link_from_node_search_record():
    record = make_search_record(html_link="https://example.com/view")
    assert ResultList._link_from_node(_FakeNode(record)) == "https://example.com/view"


def test_link_from_node_search_record_no_link():
    record = make_search_record(html_link=None)
    assert ResultList._link_from_node(_FakeNode(record)) is None


def test_link_from_node_snippet_node():
    record = make_search_record(html_link="https://example.com/link")
    node = _SnippetNode(record=record, page_number=1, text="t")
    assert ResultList._link_from_node(_FakeNode(node)) == "https://example.com/link"


def test_link_from_node_archive_node():
    node = _ArchiveNode(uri="https://archive.uri", caption="Arkiv")
    assert ResultList._link_from_node(_FakeNode(node)) == "https://archive.uri"


def test_link_from_node_archive_node_no_uri():
    node = _ArchiveNode(uri=None, caption="Arkiv")
    assert ResultList._link_from_node(_FakeNode(node)) is None


def test_link_from_node_none_data():
    assert ResultList._link_from_node(_FakeNode(None)) is None


def test_note_from_node_search_record():
    record = make_search_record(note="Important note")
    assert ResultList._note_from_node(_FakeNode(record)) == "Important note"


def test_note_from_node_search_record_none():
    record = make_search_record(note=None)
    assert ResultList._note_from_node(_FakeNode(record)) is None


def test_note_from_node_snippet_node():
    record = make_search_record(note="Snippet note")
    node = _SnippetNode(record=record, page_number=1, text="t")
    assert ResultList._note_from_node(_FakeNode(node)) == "Snippet note"


def test_note_from_node_other_data():
    assert ResultList._note_from_node(_FakeNode("random")) is None
