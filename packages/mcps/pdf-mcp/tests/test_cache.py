"""Tests for the bounded LRU cache backing the PDF and blocks caches."""

from ra_mcp_pdf_mcp.cache import LRUCache


def test_evicts_least_recently_used_over_item_bound():
    cache: LRUCache[int] = LRUCache(max_items=2)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3  # evicts "a" (LRU)
    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache
    assert len(cache) == 2


def test_access_refreshes_recency():
    cache: LRUCache[int] = LRUCache(max_items=2)
    cache["a"] = 1
    cache["b"] = 2
    _ = cache["a"]  # "a" is now most-recently-used
    cache["c"] = 3  # evicts "b", not "a"
    assert "a" in cache
    assert "b" not in cache


def test_byte_bound_evicts_when_total_exceeds():
    # Two 4-byte entries fit in 8 bytes; a third pushes the oldest out.
    cache: LRUCache[bytes] = LRUCache(max_items=100, max_bytes=8)
    cache["a"] = b"aaaa"
    cache["b"] = b"bbbb"
    cache["c"] = b"cccc"  # total would be 12 > 8 → evict "a"
    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache


def test_reassigning_same_key_updates_byte_total():
    cache: LRUCache[bytes] = LRUCache(max_items=100, max_bytes=8)
    cache["a"] = b"aaaaaaaa"  # 8 bytes, exactly at bound
    cache["a"] = b"a"  # replace: total must drop to 1, not accumulate to 9
    cache["b"] = b"bbbb"  # 1 + 4 = 5 <= 8, both stay
    assert "a" in cache
    assert "b" in cache


def test_non_bytes_values_bound_by_count_only():
    # list values weigh 0 bytes, so a byte bound never evicts them; count does.
    cache: LRUCache[list] = LRUCache(max_items=2, max_bytes=1)
    cache["a"] = [1, 2, 3]
    cache["b"] = [4, 5, 6]
    assert len(cache) == 2
    assert "a" in cache and "b" in cache
