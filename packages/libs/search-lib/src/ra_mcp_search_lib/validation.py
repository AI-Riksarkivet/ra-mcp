"""Client-side validation for user-supplied Solr query strings.

Catches obviously-malformed queries — unbalanced grouping or quoting — *before*
they reach the Riksarkivet API. A broken query like ``(((`` is otherwise accepted
by the API, which silently returns unintended results instead of erroring, so the
user has no signal that their Boolean logic was never applied.

The checks are deliberately conservative: they reject only unbalanced
parentheses/brackets and unbalanced double quotes, never valid Solr features
(wildcards ``*``, fuzzy ``~``, Boolean ``AND/OR/NOT``, ``field:value``, ranges
``[a TO b]``). A well-formed query always passes.
"""

# Solr grouping/range delimiters that must be balanced in a well-formed query.
_OPENERS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = {close: open_ for open_, close in _OPENERS.items()}


def validate_search_query(keyword: str) -> str | None:
    """Return an error message if the query is syntactically malformed, else ``None``.

    Empty/whitespace keywords are treated as valid here — that case is handled
    separately by each caller (the CLI/MCP report a dedicated "keyword required"
    error), so this function focuses only on malformed *non-empty* queries.
    """
    if not keyword or not keyword.strip():
        return None

    # Double quotes delimit phrases and must come in pairs.
    if keyword.count('"') % 2 != 0:
        return 'Unbalanced double quote (") in query. Wrap phrases in matching quotes, e.g. "Stockholms stad".'

    # Parentheses/brackets must nest and close correctly. Anything inside a quoted
    # phrase is skipped, since a quoted term may legitimately contain a lone paren.
    stack: list[str] = []
    in_quotes = False
    for char in keyword:
        if char == '"':
            in_quotes = not in_quotes
        elif in_quotes:
            continue
        elif char in _OPENERS:
            stack.append(char)
        elif char in _CLOSERS:
            if not stack or stack[-1] != _CLOSERS[char]:
                return f"Unbalanced '{char}' in query. Group Boolean logic with matching parentheses, e.g. (A OR B)."
            stack.pop()

    if stack:
        return f"Unbalanced '{stack[-1]}' in query — it is never closed. Group Boolean logic with matching parentheses, e.g. (A OR B)."

    return None
