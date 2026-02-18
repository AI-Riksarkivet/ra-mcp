"""Metadata display panel for document details."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ra_mcp_browse.models import OAIPMHMetadata
from ra_mcp_search.models import SearchRecord


class MetadataPanel(Widget):
    """Displays document metadata in a bordered panel."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = ""

    def compose(self) -> ComposeResult:
        yield Static("", id="metadata-content")

    def set_from_record(self, record: SearchRecord) -> None:
        """Populate metadata from a search record."""
        lines = [
            f"Reference: {record.metadata.reference_code or 'N/A'}",
            f"Title:     {record.get_title()}",
        ]
        if record.metadata.date:
            lines.append(f"Date:      {record.metadata.date}")
        if record.metadata.provenance:
            prov = ", ".join(p.caption or "" for p in record.metadata.provenance)
            lines.append(f"Provenance: {prov}")
        if record.metadata.archival_institution:
            inst = ", ".join(i.caption or "" for i in record.metadata.archival_institution)
            lines.append(f"Institution: {inst}")
        self._text = "\n".join(lines)
        self.query_one("#metadata-content", Static).update(self._text)

    def enrich_from_oai(self, metadata: OAIPMHMetadata) -> None:
        """Add OAI-PMH metadata to the panel."""
        extra_lines: list[str] = []
        if metadata.unitdate:
            extra_lines.append(f"Unit Date:  {metadata.unitdate}")
        if metadata.description:
            desc = metadata.description[:200]
            extra_lines.append(f"Description: {desc}")
        if metadata.repository:
            extra_lines.append(f"Repository: {metadata.repository}")
        if extra_lines:
            self._text = self._text + "\n" + "\n".join(extra_lines)
            self.query_one("#metadata-content", Static).update(self._text)
