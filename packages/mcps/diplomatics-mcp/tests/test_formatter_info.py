"""Tests for info-panel markdown formatters."""

from ra_mcp_diplomatics_mcp.formatter import format_mpo_info, format_sdhk_info


def test_format_sdhk_info_full():
    row = {
        "id": 85,
        "title": "SDHK nr 85",
        "author": "Knut Eriksson",
        "date": "11670000",
        "place": "Linköping",
        "language": "latin",
        "summary": "King Knut confirms privileges.",
        "edition": "Omnibus presentes literas inspecturis...",
        "seals": "Sigillum regis",
        "printed": "DS I 60",
    }
    md = format_sdhk_info(row)
    assert "## SDHK 85" in md
    assert "**Author:** Knut Eriksson" in md
    assert "**Date:** 11670000" in md
    assert "**Place:** Linköping" in md
    assert "**Language:** latin" in md
    assert "King Knut confirms privileges." in md
    assert "Omnibus presentes literas inspecturis..." in md
    assert "Sigillum regis" in md
    assert "DS I 60" in md


def test_format_sdhk_info_minimal():
    row = {"id": 1, "title": "", "author": "", "date": "", "summary": ""}
    md = format_sdhk_info(row)
    assert "## SDHK 1" in md
    assert "**Author:**" not in md


def test_format_mpo_info_full():
    row = {
        "id": 42,
        "manuscript_type": "Missale",
        "category": "Lit",
        "title": "Missale Lundense",
        "author": "Unknown",
        "dating": "14. Jh.",
        "origin_place": "Skandinavien?",
        "institution": "RA",
        "collection": "Östergötlands handlingar",
        "script": "Textualis",
        "material": "Pergament",
        "notation": "Quadr",
        "decoration": "Rote und blaue Lombarden.",
        "content": "1r-2v Ordo missae.",
        "format_size": "40.5 x 28.5",
        "damage": "Beschnitten am Rand.",
    }
    md = format_mpo_info(row)
    assert "## MPO 42" in md
    assert "**Type:** Missale" in md
    assert "**Category:** Lit" in md
    assert "**Dating:** 14. Jh." in md
    assert "**Script:** Textualis" in md
    assert "**Material:** Pergament" in md
    assert "Rote und blaue Lombarden." in md
    assert "1r-2v Ordo missae." in md


def test_format_mpo_info_minimal():
    row = {"id": 99, "manuscript_type": "", "category": ""}
    md = format_mpo_info(row)
    assert "## MPO 99" in md
    assert "**Type:**" not in md
