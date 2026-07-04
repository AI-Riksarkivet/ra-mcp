"""Tests for the Specialsök plain-text formatters.

The formatters are pure sync functions that take a SearchResult (a dataclass
whose ``records`` is a list of plain dicts) and return a plain-text string.
Each dataset has its own formatter; they all share the header/footer helpers,
so every test asserts on concrete substrings the formatter actually emits.
"""

from __future__ import annotations

from ra_mcp_specialsok_lib.search_operations import SearchResult
from ra_mcp_specialsok_mcp.formatter import (
    format_fangrullor_results,
    format_flygvapen_results,
    format_kurhuset_results,
    format_press_results,
    format_video_results,
)


def _result(records: list[dict], *, keyword: str = "test", total: int | None = None, offset: int = 0, limit: int = 25) -> SearchResult:
    """Build a SearchResult, defaulting total_hits to len(records)."""
    return SearchResult(
        records=records,
        total_hits=len(records) if total is None else total,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Realistic sample records (dicts with the exact keys each formatter reads)
# ---------------------------------------------------------------------------


def _flygvapen_record() -> dict:
    return {
        "datum": "1944-05-12",
        "fpl_typ": "J 22",
        "fpl_nr": "22156",
        "forband_klartext": "F 9 Göteborg",
        "motor_typ": "SFA STWC-3",
        "havplats": "Säve",
        "bes_ant": "1",
        "ant_omk": "0",
        "klassning": "Haveri",
        "sammanfattning": "Motorstopp vid start, nödlandning på fältet utan personskador.",
    }


def _fangrullor_record() -> dict:
    return {
        "fornamn": "Anna",
        "efternamn": "Andersdotter",
        "alder": "27",
        "hemort": "Brunflo",
        "brott": "Stöld",
        "ar": "1854",
        "nummer": "142",
    }


def _kurhuset_record() -> dict:
    return {
        "fornamn": "Erik",
        "efternamn": "Persson",
        "alder": "34",
        "titel": "Dräng",
        "familj": "Gift",
        "hemort_by": "Nästgård",
        "hemort_socken": "Frösö",
        "inskrivningsdatum": "1840-03-01",
        "utskrivningsdatum": "1840-04-15",
        "utskrivningsstatus": "Frisk",
        "vardtid": "45",
        "sjukdom": "Syfilis",
        "sjukdomsbeskrivning": "Utslag på huden och sår i munnen.",
        "sjukdomsbehandling": "Kvicksilver.",
        "anmarkning": "Återfall noterat.",
    }


def _press_record() -> dict:
    return {
        "datum": "2001-09-14",
        "aar": "2001",
        "titel": "Regeringens pressträff",
        "arkivbildare": "Statsrådsberedningen",
        "v_ra_nr": "RA-2001-0914",
        "innehaall": "Statsministern kommenterar det säkerhetspolitiska läget.",
        "anmaerkning": "Ljudupptagning saknas.",
    }


def _video_record() -> dict:
    return {
        "butiksnamn": "Videohörnan",
        "firmanamn": "Videohörnan AB",
        "besoeksadress": "Storgatan 5",
        "ort": "Östersund",
        "kommun": "Östersund",
        "laen": "Jämtland",
        "landsdel": "Norrland",
        "aktiv": "Ja",
        "reg_nr": "Z-1234",
    }


# ---------------------------------------------------------------------------
# Flygvapenhaverier
# ---------------------------------------------------------------------------


def test_flygvapen_no_results_at_offset_zero():
    out = format_flygvapen_results(_result([], keyword="krasch"))
    assert out == "No Flygvapenhaverier results found for 'krasch'."


def test_flygvapen_no_more_results_at_nonzero_offset():
    out = format_flygvapen_results(_result([], keyword="krasch", total=200, offset=50))
    assert "No more Flygvapenhaverier results for 'krasch' at offset 50" in out
    assert "Total found: 200" in out


def test_flygvapen_single_record():
    out = format_flygvapen_results(_result([_flygvapen_record()], keyword="J 22"))
    assert "Flygvapenhaverier search results for 'J 22': showing 1 of 1 records (offset 0)" in out
    assert "--- Flygvapenhaveri ---" in out
    assert "Date: 1944-05-12" in out
    assert "Aircraft: J 22" in out
    assert "Aircraft no: 22156" in out
    assert "Unit: F 9 Göteborg" in out
    assert "Engine: SFA STWC-3" in out
    assert "Crash site: Säve" in out
    assert "Crew: 1" in out
    assert "Casualties: 0" in out
    assert "Classification: Haveri" in out
    assert "Summary: Motorstopp vid start" in out


def test_flygvapen_multiple_records_shows_count():
    recs = [_flygvapen_record(), _flygvapen_record()]
    out = format_flygvapen_results(_result(recs, keyword="J 22"))
    assert "showing 2 of 2 records" in out
    assert out.count("--- Flygvapenhaveri ---") == 2


def test_flygvapen_missing_optional_fields_omits_labels():
    # Only aircraft type present; every other field absent from the dict.
    out = format_flygvapen_results(_result([{"fpl_typ": "SK 16"}], keyword="SK 16"))
    assert "Aircraft: SK 16" in out
    assert "Date:" not in out
    assert "Unit:" not in out
    assert "Summary:" not in out
    assert "Casualties:" not in out


def test_flygvapen_long_summary_truncated_to_200_chars():
    long_text = "A" * 500
    out = format_flygvapen_results(_result([{"sammanfattning": long_text}], keyword="x"))
    summary_line = next(line for line in out.splitlines() if line.startswith("Summary: "))
    body = summary_line[len("Summary: ") :]
    assert body.endswith("...")
    assert len(body) == 200


# ---------------------------------------------------------------------------
# Fångrullor
# ---------------------------------------------------------------------------


def test_fangrullor_no_results():
    out = format_fangrullor_results(_result([], keyword="tjuv"))
    assert out == "No Fångrullor results found for 'tjuv'."


def test_fangrullor_single_record_joins_name():
    out = format_fangrullor_results(_result([_fangrullor_record()], keyword="Anna"))
    assert "--- Fångrulle ---" in out
    assert "Name: Anna Andersdotter" in out
    assert "Age: 27" in out
    assert "Home parish: Brunflo" in out
    assert "Crime: Stöld" in out
    assert "Year: 1854" in out
    assert "Number: 142" in out


def test_fangrullor_name_uses_only_present_parts():
    # Only surname present -> name is just the surname, no leading space.
    out = format_fangrullor_results(_result([{"efternamn": "Larsson"}], keyword="Larsson"))
    assert "Name: Larsson" in out
    assert "Name:  Larsson" not in out


def test_fangrullor_all_name_parts_missing_omits_name_label():
    out = format_fangrullor_results(_result([{"brott": "Mord"}], keyword="Mord"))
    assert "Crime: Mord" in out
    assert "Name:" not in out


def test_fangrullor_multiple_records():
    recs = [_fangrullor_record(), _fangrullor_record(), _fangrullor_record()]
    out = format_fangrullor_results(_result(recs, keyword="Anna"))
    assert "showing 3 of 3 records" in out
    assert out.count("--- Fångrulle ---") == 3


# ---------------------------------------------------------------------------
# Kurhuset
# ---------------------------------------------------------------------------


def test_kurhuset_no_results():
    out = format_kurhuset_results(_result([], keyword="syfilis"))
    assert out == "No Kurhuset results found for 'syfilis'."


def test_kurhuset_single_record():
    out = format_kurhuset_results(_result([_kurhuset_record()], keyword="Erik"))
    assert "--- Kurhuset patient ---" in out
    assert "Name: Erik Persson" in out
    assert "Age: 34" in out
    assert "Title: Dräng" in out
    assert "Family: Gift" in out
    assert "Home (village): Nästgård" in out
    assert "Home (parish): Frösö" in out
    assert "Admitted: 1840-03-01" in out
    assert "Discharged: 1840-04-15" in out
    assert "Outcome: Frisk" in out
    assert "Days: 45" in out
    assert "Disease: Syfilis" in out
    assert "Description: Utslag på huden" in out
    assert "Treatment: Kvicksilver." in out
    assert "Note: Återfall noterat." in out


def test_kurhuset_missing_optional_fields_omits_labels():
    out = format_kurhuset_results(_result([{"sjukdom": "Frossa"}], keyword="Frossa"))
    assert "Disease: Frossa" in out
    assert "Name:" not in out
    assert "Description:" not in out
    assert "Treatment:" not in out
    assert "Note:" not in out


def test_kurhuset_long_description_and_treatment_truncated():
    rec = {"sjukdomsbeskrivning": "B" * 400, "sjukdomsbehandling": "C" * 400}
    out = format_kurhuset_results(_result([rec], keyword="x"))
    desc = next(line for line in out.splitlines() if line.startswith("Description: "))[len("Description: ") :]
    treat = next(line for line in out.splitlines() if line.startswith("Treatment: "))[len("Treatment: ") :]
    assert len(desc) == 200
    assert desc.endswith("...")
    assert len(treat) == 200
    assert treat.endswith("...")


# ---------------------------------------------------------------------------
# Presskonferenser
# ---------------------------------------------------------------------------


def test_press_no_results():
    out = format_press_results(_result([], keyword="regering"))
    assert out == "No Presskonferenser results found for 'regering'."


def test_press_single_record():
    out = format_press_results(_result([_press_record()], keyword="regering"))
    assert "--- Presskonferens ---" in out
    assert "Date: 2001-09-14" in out
    assert "Year: 2001" in out
    assert "Title: Regeringens pressträff" in out
    assert "Archive: Statsrådsberedningen" in out
    assert "RA nr: RA-2001-0914" in out
    assert "Content: Statsministern kommenterar" in out
    assert "Note: Ljudupptagning saknas." in out


def test_press_missing_optional_fields_omits_labels():
    out = format_press_results(_result([{"titel": "Kort möte"}], keyword="möte"))
    assert "Title: Kort möte" in out
    assert "Date:" not in out
    assert "Content:" not in out
    assert "Note:" not in out


def test_press_long_content_truncated():
    out = format_press_results(_result([{"innehaall": "D" * 300}], keyword="x"))
    content = next(line for line in out.splitlines() if line.startswith("Content: "))[len("Content: ") :]
    assert len(content) == 200
    assert content.endswith("...")


# ---------------------------------------------------------------------------
# Videobutiker
# ---------------------------------------------------------------------------


def test_video_no_results():
    out = format_video_results(_result([], keyword="video"))
    assert out == "No Videobutiker results found for 'video'."


def test_video_single_record():
    out = format_video_results(_result([_video_record()], keyword="video"))
    assert "--- Videobutik ---" in out
    assert "Store: Videohörnan" in out
    assert "Company: Videohörnan AB" in out
    assert "Address: Storgatan 5" in out
    assert "City: Östersund" in out
    assert "Municipality: Östersund" in out
    assert "County: Jämtland" in out
    assert "Region: Norrland" in out
    assert "Active: Ja" in out
    assert "Reg nr: Z-1234" in out


def test_video_missing_optional_fields_omits_labels():
    out = format_video_results(_result([{"butiksnamn": "Filmboden"}], keyword="Filmboden"))
    assert "Store: Filmboden" in out
    assert "Company:" not in out
    assert "City:" not in out
    assert "Reg nr:" not in out


def test_video_multiple_records():
    recs = [_video_record(), _video_record()]
    out = format_video_results(_result(recs, keyword="video"))
    assert "showing 2 of 2 records" in out
    assert out.count("--- Videobutik ---") == 2


# ---------------------------------------------------------------------------
# Shared header/footer behaviour (exercised via one representative formatter)
# ---------------------------------------------------------------------------


def test_footer_shown_when_more_results_available():
    # 2 shown, limit 25, but 100 total -> next offset 25 < 100 -> hint present.
    out = format_video_results(_result([_video_record(), _video_record()], keyword="v", total=100, offset=0, limit=25))
    assert "More results available. Use offset=25 to see the next page." in out


def test_footer_absent_when_all_results_shown():
    out = format_video_results(_result([_video_record()], keyword="v", total=1, offset=0, limit=25))
    assert "More results available" not in out


def test_footer_offset_accumulates_with_current_offset():
    # offset 25 + limit 25 = 50 < 60 -> next page hint at offset 50.
    out = format_flygvapen_results(_result([_flygvapen_record()], keyword="j", total=60, offset=25, limit=25))
    assert "Use offset=50 to see the next page." in out


def test_header_reports_offset_and_partial_count():
    recs = [_press_record()]
    out = format_press_results(_result(recs, keyword="möte", total=42, offset=10, limit=25))
    assert "showing 1 of 42 records (offset 10)" in out
