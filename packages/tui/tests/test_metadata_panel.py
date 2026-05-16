"""Tests for the MetadataPanel widget."""

from textual.app import App, ComposeResult

from ra_mcp_oai_pmh_lib import OAIPMHMetadata
from ra_mcp_search_lib.models import GenericReference

from ra_mcp_tui.widgets.metadata_panel import MetadataPanel

from conftest import make_search_record


class MetadataPanelApp(App):
    def compose(self) -> ComposeResult:
        yield MetadataPanel(id="meta")


async def test_metadata_panel_set_from_record():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record(
            reference_code="SE/RA/420422/01",
            caption="Test Title",
            date="1742",
        )
        panel.set_from_record(record)
        await pilot.pause()
        assert "SE/RA/420422/01" in panel._text
        assert "Test Title" in panel._text
        assert "1742" in panel._text


async def test_metadata_panel_no_date():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record(date=None)
        panel.set_from_record(record)
        await pilot.pause()
        assert "Date:" not in panel._text


async def test_metadata_panel_provenance():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record(
            provenance=[GenericReference(caption="Svea hovrätt")],
        )
        panel.set_from_record(record)
        await pilot.pause()
        assert "Svea hovrätt" in panel._text


async def test_metadata_panel_institution():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record(
            archival_institution=[GenericReference(caption="Riksarkivet")],
        )
        panel.set_from_record(record)
        await pilot.pause()
        assert "Riksarkivet" in panel._text


async def test_metadata_panel_no_reference_code():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record(reference_code=None)
        panel.set_from_record(record)
        await pilot.pause()
        assert "N/A" in panel._text


async def test_metadata_panel_enrich_from_oai():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record()
        panel.set_from_record(record)
        await pilot.pause()

        oai = OAIPMHMetadata(
            identifier="SE/RA/420422/01",
            unitdate="1700-1750",
            description="A detailed description of the document",
            repository="Riksarkivet, Marieberg",
        )
        panel.enrich_from_oai(oai)
        await pilot.pause()
        assert "1700-1750" in panel._text
        assert "A detailed description" in panel._text
        assert "Riksarkivet, Marieberg" in panel._text


async def test_metadata_panel_enrich_from_oai_empty():
    """OAI metadata with no optional fields should not add extra lines."""
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record()
        panel.set_from_record(record)
        original_text = panel._text
        await pilot.pause()

        oai = OAIPMHMetadata(identifier="SE/RA/420422/01")
        panel.enrich_from_oai(oai)
        await pilot.pause()
        assert panel._text == original_text


async def test_metadata_panel_enrich_truncates_description():
    async with MetadataPanelApp().run_test() as pilot:
        panel = pilot.app.query_one(MetadataPanel)
        record = make_search_record()
        panel.set_from_record(record)

        long_desc = "A" * 500
        oai = OAIPMHMetadata(identifier="id", description=long_desc)
        panel.enrich_from_oai(oai)
        await pilot.pause()
        assert len(panel._text) < len(long_desc) + 200
