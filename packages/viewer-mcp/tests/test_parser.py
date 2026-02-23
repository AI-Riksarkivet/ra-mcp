"""Tests for ALTO v4 and PAGE XML parsing."""

from ra_mcp_viewer_mcp.parser import detect_and_parse, parse_alto_xml, parse_page_xml


# ── ALTO word-level (30002056) ──────────────────────────────────────────


def test_parse_alto_word_level(alto_word_level_xml):
    data = parse_alto_xml(alto_word_level_xml)

    assert data.page_width == 5379
    assert data.page_height == 4395

    assert len(data.text_lines) == 75

    # First line joins two words
    first = data.text_lines[0]
    assert first.transcription == "sedan han"
    assert first.id == "_30002056_00010_region0_line0"

    # No WC attributes → confidence should be None for all lines
    for line in data.text_lines:
        assert line.confidence is None


# ── ALTO line-level (451511) ────────────────────────────────────────────


def test_parse_alto_line_level(alto_line_level_xml):
    data = parse_alto_xml(alto_line_level_xml)

    assert data.page_width == 1511
    assert data.page_height == 2413
    assert len(data.text_lines) == 18

    first = data.text_lines[0]
    assert first.id == "451511_1512_01_textline0"
    assert first.transcription == "Mommouth den 29 1882."
    assert first.confidence is not None
    assert abs(first.confidence - 0.9862444319434949) < 1e-6


# ── PAGE XML (451511) ──────────────────────────────────────────────────


def test_parse_page_xml(page_xml):
    data = parse_page_xml(page_xml)

    assert data.page_width == 1511
    assert data.page_height == 2413
    assert len(data.text_lines) == 18

    first = data.text_lines[0]
    assert first.id == "451511_1512_01_textline0"
    assert first.transcription == "Mommouth den 29 1882."
    assert first.confidence is not None
    assert abs(first.confidence - 0.9862444319434949) < 1e-6

    # Bounding box computed from polygon coords
    assert first.hpos == 355
    assert first.vpos == 203


# ── Auto-detection ─────────────────────────────────────────────────────


def test_detect_and_parse_alto(alto_line_level_xml):
    data = detect_and_parse(alto_line_level_xml)
    assert len(data.text_lines) == 18
    assert data.text_lines[0].transcription == "Mommouth den 29 1882."


def test_detect_and_parse_page(page_xml):
    data = detect_and_parse(page_xml)
    assert len(data.text_lines) == 18
    assert data.text_lines[0].transcription == "Mommouth den 29 1882."


# ── Cross-format consistency ───────────────────────────────────────────


def test_alto_and_page_same_output(alto_line_level_xml, page_xml):
    alto = parse_alto_xml(alto_line_level_xml)
    page = parse_page_xml(page_xml)

    assert alto.page_width == page.page_width
    assert alto.page_height == page.page_height
    assert len(alto.text_lines) == len(page.text_lines)

    for a, p in zip(alto.text_lines, page.text_lines, strict=True):
        assert a.id == p.id
        assert a.transcription == p.transcription
        # Confidence values come from the same source data
        if a.confidence is not None and p.confidence is not None:
            assert abs(a.confidence - p.confidence) < 1e-6


# ── ALTO Transkribus (R0001203_00010) ─────────────────────────────────


def test_parse_alto_transkribus(alto_transkribus_xml):
    """Transkribus ALTO: no Shape/Polygon on TextLines, polygon from BASELINE."""
    data = parse_alto_xml(alto_transkribus_xml)

    assert data.page_width == 4787
    assert data.page_height == 3684
    assert len(data.text_lines) == 58

    first = data.text_lines[0]
    assert first.id == "line_1688506941581_6250"
    assert first.transcription == "8."
    assert first.hpos == 293
    assert first.vpos == 138
    assert first.width == 121
    assert first.height == 185

    # Polygon synthesized from BASELINE with ascent/descent offsets (not bbox)
    # BASELINE="306,290 420,290" → top offset -40, bottom offset +15
    assert first.polygon == "306,250 420,250 420,305 306,305"

    # No WC attributes in Transkribus output
    for line in data.text_lines:
        assert line.confidence is None


def test_parse_alto_transkribus_joins_words(alto_transkribus_xml):
    """Transkribus ALTO joins multiple String elements per TextLine."""
    data = parse_alto_xml(alto_transkribus_xml)

    # Second line (r2l1) has many String children that should be joined
    second = data.text_lines[1]
    assert second.id == "r2l1"
    assert "Om" in second.transcription
    assert "Han" in second.transcription
    assert "icke" in second.transcription


def test_detect_and_parse_transkribus(alto_transkribus_xml):
    data = detect_and_parse(alto_transkribus_xml)
    assert len(data.text_lines) == 58
    assert data.text_lines[0].transcription == "8."
