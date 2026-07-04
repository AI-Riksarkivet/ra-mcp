"""Tests for the LanceDB-backed guide search (Swedish FTS + bbox highlighting)."""

import ra_mcp_pdf_mcp.guide_index as gi
from ra_mcp_pdf_mcp.cache import LRUCache


def _cache(pages_by_url: dict[str, list[dict]]) -> LRUCache:
    c: LRUCache = LRUCache(max_items=100)
    for url, pages in pages_by_url.items():
        c[url] = pages
    return c


def _page(page_index: int, blocks: list[dict]) -> dict:
    return {"page": page_index, "bbox": [0, 0, 100, 100], "children": blocks}


def _block(text: str, bbox: list[int]) -> dict:
    return {"html": f"<p>{text}</p>", "bbox": bbox, "block_type": "Text"}


def test_inflected_query_matches_base_form():
    # The whole point of Swedish FTS: an inflected QUERY matches the base form in
    # the text. The old substring scan could NOT do this — "hästar" is not a
    # substring of "en häst i hagen" — so it would return zero.
    gi._indexed = None
    cache = _cache({"g://x": [_page(0, [_block("en häst i hagen", [1, 1, 1, 1])])]})
    assert gi.ensure_guide_index(cache) is True
    res = gi.search_guide_index("hästar")
    assert res.total_matches >= 1
    # bbox is preserved so the viewer can still highlight the block
    assert res.page_matches[0].blocks[0].bbox == [1, 1, 1, 1]


def test_stemming_matches_inflections_across_guides():
    gi._indexed = None
    cache = _cache(
        {
            "g://a": [
                _page(0, [_block("om kungens råd och beslut", [1, 2, 3, 4])]),
                _page(1, [_block("helt annat om bönder", [5, 6, 7, 8])]),
            ],
            "g://b": [_page(0, [_block("kungar regerade landet", [9, 9, 9, 9])])],
        }
    )
    gi.ensure_guide_index(cache)
    # "kung" stems to match "kungens" (guide a) and "kungar" (guide b)
    assert gi.search_guide_index("kung", guide_url="g://a").total_matches >= 1
    assert gi.search_guide_index("kung", guide_url="g://b").total_matches >= 1
    # the non-matching page (bönder) is not returned
    res_a = gi.search_guide_index("kung", guide_url="g://a")
    assert all(pm.page_index == 0 for pm in res_a.page_matches)


def test_guide_url_filter_isolates_a_single_guide():
    gi._indexed = None
    cache = _cache(
        {
            "g://a": [_page(0, [_block("kungens kansli", [0, 0, 1, 1])])],
            "g://b": [_page(0, [_block("kungens hov", [2, 2, 3, 3])])],
        }
    )
    gi.ensure_guide_index(cache)
    res_b = gi.search_guide_index("kung", guide_url="g://b")
    assert res_b.total_matches >= 1
    assert res_b.page_matches[0].blocks[0].bbox == [2, 2, 3, 3]


def test_no_match_returns_empty():
    gi._indexed = None
    cache = _cache({"g://y": [_page(0, [_block("bönder och jordbruk", [0, 0, 1, 1])])]})
    gi.ensure_guide_index(cache)
    res = gi.search_guide_index("flygplan")
    assert res.total_matches == 0
    assert res.page_matches == []


def test_empty_cache_is_not_searchable():
    gi._indexed = None
    assert gi.ensure_guide_index(LRUCache(max_items=100)) is False
