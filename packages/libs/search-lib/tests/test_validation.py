"""Tests for client-side Solr query validation."""

import pytest

from ra_mcp_search_lib.validation import validate_search_query


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("Stockholm", id="plain-term"),
        pytest.param("troll*", id="wildcard"),
        pytest.param("stockholm~1", id="fuzzy"),
        pytest.param("(Stockholm OR Göteborg)", id="boolean-group"),
        pytest.param("(A AND (B OR C))", id="nested-group"),
        pytest.param('"Stockholms stad"', id="phrase"),
        pytest.param('"term1 term2"~10', id="proximity"),
        pytest.param("[1700 TO 1750]", id="range-bracket"),
        pytest.param("text:Stockholm", id="field-value"),
        pytest.param('"a (paren) inside quotes"', id="paren-inside-quotes"),
        pytest.param("", id="empty"),
        pytest.param("   ", id="whitespace-only"),
    ],
)
def test_valid_queries_pass(query):
    assert validate_search_query(query) is None


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("(((", id="triple-open-paren"),
        pytest.param("(A OR B", id="missing-close-paren"),
        pytest.param("A OR B)", id="stray-close-paren"),
        pytest.param(")A(", id="closed-before-open"),
        pytest.param("[1700 TO 1750", id="unclosed-bracket"),
        pytest.param("(A OR B]", id="mismatched-delimiters"),
    ],
)
def test_malformed_grouping_is_rejected(query):
    error = validate_search_query(query)
    assert error is not None
    assert "Unbalanced" in error


def test_unbalanced_quotes_are_rejected():
    error = validate_search_query('"Stockholm')
    assert error is not None
    assert "double quote" in error.lower()
