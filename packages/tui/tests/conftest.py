"""Shared fixtures for TUI package tests."""

from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_oai_pmh_lib import OAIPMHMetadata
from ra_mcp_search_lib.models import (
    DocumentLinks,
    GenericReference,
    Metadata,
    PageInfo,
    RecordsResponse,
    SearchRecord,
    SearchResult,
    Snippet,
    TranscribedText,
)


REFERENCE_CODE = "SE/RA/420422/01"
MANIFEST_ID = "R0001203"


def make_page_context(
    page_number: int = 1,
    text: str = "some transcribed text",
    reference_code: str = REFERENCE_CODE,
) -> PageContext:
    return PageContext(
        page_number=page_number,
        page_id=f"_{page_number:05d}",
        reference_code=reference_code,
        full_text=text,
        alto_url=f"https://sok.riksarkivet.se/dokument/alto/{MANIFEST_ID}/{MANIFEST_ID}_{page_number:05d}.xml",
        image_url=f"https://lbiiif.riksarkivet.se/arkis!{MANIFEST_ID}_{page_number:05d}/full/max/0/default.jpg",
        bildvisning_url=f"https://sok.riksarkivet.se/bildvisning/{MANIFEST_ID}_{page_number:05d}",
    )


def make_search_record(
    *,
    record_id: str = "rec-1",
    reference_code: str = REFERENCE_CODE,
    caption: str = "Test document title",
    date: str | None = "1742",
    snippets: list[Snippet] | None = None,
    num_total: int = 3,
    html_link: str | None = "https://sok.riksarkivet.se/bildvisning/R0001203",
    note: str | None = None,
    provenance: list[GenericReference] | None = None,
    hierarchy: list[GenericReference] | None = None,
    archival_institution: list[GenericReference] | None = None,
) -> SearchRecord:
    if snippets is None:
        snippets = [
            Snippet(
                text="found <em>trolldom</em> on this page",
                score=1.0,
                pages=[PageInfo(id="_00007")],
            ),
        ]
    return SearchRecord(
        id=record_id,
        objectType="Record",
        type="Volume",
        caption=caption,
        metadata=Metadata(
            referenceCode=reference_code,
            date=date,
            note=note,
            provenance=provenance,
            hierarchy=hierarchy,
            archivalInstitution=archival_institution,
        ),
        transcribedText=TranscribedText(numTotal=num_total, snippets=snippets),
        _links=DocumentLinks(html=html_link) if html_link else None,
    )


def make_search_result(
    records: list[SearchRecord] | None = None,
    total_hits: int = 1,
    keyword: str = "trolldom",
    offset: int = 0,
    limit: int = 25,
) -> SearchResult:
    if records is None:
        records = [make_search_record()]
    return SearchResult(
        response=RecordsResponse(items=records, totalHits=total_hits),
        transcribed_text=keyword,
        limit=limit,
        offset=offset,
    )


def make_browse_result(
    pages: list[PageContext] | None = None,
    reference_code: str = REFERENCE_CODE,
    pages_requested: str = "1-20",
    manifest_id: str | None = MANIFEST_ID,
    oai_metadata: OAIPMHMetadata | None = None,
) -> BrowseResult:
    if pages is None:
        pages = [make_page_context(i) for i in range(1, 4)]
    return BrowseResult(
        contexts=pages,
        reference_code=reference_code,
        pages_requested=pages_requested,
        manifest_id=manifest_id,
        oai_metadata=oai_metadata,
    )
