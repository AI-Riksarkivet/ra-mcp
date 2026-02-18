"""List widgets for search results and document pages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Label, LoadingIndicator, Tree
from textual.widgets._tree import TreeNode

from ra_mcp_browse.models import PageContext
from ra_mcp_common.utils.formatting import page_id_to_number
from ra_mcp_search.models import SearchRecord

_EM_RE = re.compile(r"<em>(.*?)</em>")


@dataclass
class _ArchiveNode:
    """Data for an intermediate tree node (archive/series level)."""

    uri: str | None = None
    caption: str | None = None


@dataclass
class _SnippetNode:
    """Data for a snippet leaf node (search hit on a specific page)."""

    record: SearchRecord
    page_number: int
    text: str


class ResultList(Widget):
    """Displays search results as a tree grouped by reference code segments."""

    class SnippetSelected(Message):
        """Fired when a snippet node is selected (navigates to a specific page)."""

        def __init__(self, record: SearchRecord, page_number: int) -> None:
            super().__init__()
            self.record = record
            self.page_number = page_number

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._records: list[SearchRecord] = []
        self._status_text = ""

    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="result-loading")
        yield Label("", id="no-results")
        yield Tree("Results", id="result-tree")
        yield Label("", id="result-status")
        yield Label("", id="result-note")

    def on_mount(self) -> None:
        self.query_one("#result-loading").display = False
        self.query_one("#no-results", Label).display = False
        self.query_one("#result-note", Label).display = False
        tree = self.query_one("#result-tree", Tree)
        tree.show_root = False
        tree.guide_depth = 3

    def set_results(self, records: list[SearchRecord], total_hits: int, keyword: str, offset: int = 0, page_size: int = 25) -> None:
        """Populate the tree with search results grouped by reference code."""
        self._records = records
        self.query_one("#result-loading").display = False
        tree = self.query_one("#result-tree", Tree)
        no_results = self.query_one("#no-results", Label)
        tree.clear()
        if not records:
            tree.display = False
            no_results.update(f"No results found for '{keyword}'\n\nTry different keywords, wildcards (e.g. troll*), or switch search mode (m)")
            no_results.display = True
            self._status_text = ""
            self.query_one("#result-status", Label).update("")
            return
        no_results.display = False
        tree.display = True
        self._build_tree(tree, records)
        start = offset + 1
        end = offset + len(records)
        self._status_text = f" {start}-{end} of {total_hits} results for '{keyword}'"
        if total_hits > page_size:
            page_num = offset // page_size + 1
            total_pages = (total_hits + page_size - 1) // page_size
            self._status_text += f"  (page {page_num}/{total_pages}, n/p to navigate)"
        self.query_one("#result-status", Label).update(self._status_text)

    def _build_tree(self, tree: Tree, records: list[SearchRecord]) -> None:
        sorted_records = sorted(records, key=lambda r: r.metadata.reference_code or "")
        path_nodes: dict[tuple[str, ...], TreeNode] = {}

        for record in sorted_records:
            parts = (record.metadata.reference_code or "").split("/")
            # Create/find intermediate nodes with hierarchy metadata
            for depth in range(len(parts) - 1):
                path_key = tuple(parts[: depth + 1])
                if path_key not in path_nodes:
                    parent_key = tuple(parts[:depth])
                    parent = path_nodes.get(parent_key) if parent_key else tree.root
                    if parent is None:
                        parent = tree.root
                    node_data = self._node_metadata(record, depth)
                    segment = parts[depth]
                    label = node_data.caption if node_data and node_data.caption else segment
                    path_nodes[path_key] = parent.add(label, data=node_data)

            # Add record node (branch so snippets can be children)
            parent_key = tuple(parts[:-1])
            parent = path_nodes.get(parent_key) if parent_key else tree.root
            if parent is None:
                parent = tree.root
            title = self._truncate(record.get_title(), 50)
            hits = record.get_total_hits()
            date = record.metadata.date or ""
            date_str = f"  ({date})" if date else ""
            label = f"{title}{date_str}  [{hits} hits]"
            record_node = parent.add(label, data=record)

            # Add snippet leaves under the record node
            self._add_snippets(record_node, record)

        tree.root.expand_all()

    def _add_snippets(self, record_node: TreeNode, record: SearchRecord) -> None:
        if not record.transcribed_text:
            return
        snippets = sorted(
            record.transcribed_text.snippets,
            key=lambda s: page_id_to_number(s.pages[0].id) if s.pages else 0,
        )
        for snippet in snippets:
            page_num = page_id_to_number(snippet.pages[0].id) if snippet.pages else 0
            label = self._styled_snippet(snippet.text, page_num)
            record_node.add_leaf(label, data=_SnippetNode(record=record, page_number=page_num, text=snippet.text))

    @staticmethod
    def _styled_snippet(raw: str, page_num: int) -> Text:
        """Build a Rich Text label with <em> regions highlighted."""
        prefix = f"p.{page_num}: "
        plain = raw.replace("\n", " ").strip()
        result = Text(prefix, style="dim")
        for i, part in enumerate(_EM_RE.split(plain)):
            if i % 2 == 1:
                result.append(part, style="bold #C9A96E")
            else:
                result.append(part)
        result.truncate(200, overflow="ellipsis")
        return result

    @staticmethod
    def _node_metadata(record: SearchRecord, depth: int) -> _ArchiveNode | None:
        """Extract metadata for an intermediate node at the given depth.

        Depth mapping (ref code ``SE/RA/420422/01/...``):
        - 0 (SE)  → country code, no metadata
        - 1 (RA)  → archival_institution
        - 2       → hierarchy[0] or provenance (archive/fond level)
        - 3+      → hierarchy[depth - 2]
        """
        if depth == 0:
            return None
        if depth == 1 and record.metadata.archival_institution:
            inst = record.metadata.archival_institution[0]
            return _ArchiveNode(uri=inst.uri, caption=inst.caption)
        hierarchy_idx = depth - 2
        if hierarchy_idx >= 0 and record.metadata.hierarchy and hierarchy_idx < len(record.metadata.hierarchy):
            h = record.metadata.hierarchy[hierarchy_idx]
            return _ArchiveNode(uri=h.uri, caption=h.caption)
        # Fallback: use provenance for the archive level when hierarchy is missing
        if depth == 2 and record.metadata.provenance:
            prov = record.metadata.provenance[0]
            return _ArchiveNode(uri=prov.uri, caption=prov.caption)
        return None

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        return text[: max_len - 1] + "\u2026" if len(text) > max_len else text

    def show_loading(self, keyword: str) -> None:
        """Show loading state with animated indicator."""
        self.query_one("#result-tree", Tree).display = False
        self.query_one("#no-results", Label).display = False
        self.query_one("#result-loading").display = True
        status = self.query_one("#result-status", Label)
        status.update(f" Searching for '{keyword}'...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        self.query_one("#result-loading").display = False
        tree = self.query_one("#result-tree", Tree)
        tree.display = True
        tree.clear()
        status = self.query_one("#result-status", Label)
        status.update(f" Error: {message}")

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        node = event.node
        ref = self._ref_from_node(node)
        link = self._link_from_node(node)
        if ref and link:
            self.query_one("#result-status", Label).update(f" {ref}  {link}  (o to open)")
        elif ref:
            self.query_one("#result-status", Label).update(f" {ref}")
        elif link:
            self.query_one("#result-status", Label).update(f" {link}  (o to open)")
        else:
            self.query_one("#result-status", Label).update(self._status_text)
        # Show note for highlighted record
        note = self._note_from_node(node)
        note_label = self.query_one("#result-note", Label)
        if note:
            note_label.update(note)
            note_label.display = True
        else:
            note_label.display = False

    @staticmethod
    def _ref_from_node(node: TreeNode) -> str | None:
        if isinstance(node.data, SearchRecord):
            return node.data.metadata.reference_code
        if isinstance(node.data, _SnippetNode):
            return node.data.record.metadata.reference_code
        return None

    @staticmethod
    def _note_from_node(node: TreeNode) -> str | None:
        if isinstance(node.data, SearchRecord):
            return node.data.metadata.note
        if isinstance(node.data, _SnippetNode):
            return node.data.record.metadata.note
        return None

    def get_highlighted_record(self) -> SearchRecord | None:
        """Return the record for the currently highlighted node."""
        tree = self.query_one("#result-tree", Tree)
        node = tree.cursor_node
        if node is None:
            return None
        if isinstance(node.data, SearchRecord):
            return node.data
        if isinstance(node.data, _SnippetNode):
            return node.data.record
        return None

    def get_highlighted_link(self) -> str | None:
        """Return a link for the currently highlighted node (leaf or intermediate)."""
        tree = self.query_one("#result-tree", Tree)
        node = tree.cursor_node
        if node is not None:
            return self._link_from_node(node)
        return None

    @staticmethod
    def _link_from_node(node: TreeNode) -> str | None:
        if isinstance(node.data, SearchRecord):
            return node.data.links.html if node.data.links and node.data.links.html else None
        if isinstance(node.data, _SnippetNode):
            rec = node.data.record
            return rec.links.html if rec.links and rec.links.html else None
        if isinstance(node.data, _ArchiveNode):
            return node.data.uri
        return None

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node
        if isinstance(node.data, _SnippetNode):
            self.post_message(self.SnippetSelected(record=node.data.record, page_number=node.data.page_number))


class PageList(Widget):
    """Displays document pages as a data table."""

    AUTOLOAD_THRESHOLD = 3
    HIT_MARKER = ">>>"

    class Selected(Message):
        """Fired when a page is selected."""

        def __init__(self, page: PageContext, all_pages: list[PageContext]) -> None:
            super().__init__()
            self.page = page
            self.all_pages = all_pages

    class NearEnd(Message):
        """Fired when the cursor is near the end of the list."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pages: list[PageContext] = []
        self._hit_pages: set[int] = set()

    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="page-loading")
        yield DataTable(id="page-table", cursor_type="row")
        yield Label("", id="page-status")

    def on_mount(self) -> None:
        self.query_one("#page-loading").display = False
        table = self.query_one("#page-table", DataTable)
        table.add_columns("Hit", "Page", "Preview")

    def set_hit_pages(self, hit_pages: set[int]) -> None:
        """Set which page numbers have search hits."""
        self._hit_pages = hit_pages

    def set_pages(self, pages: list[PageContext]) -> None:
        """Populate the table with document pages."""
        self._pages = list(pages)
        self.query_one("#page-loading").display = False
        table = self.query_one("#page-table", DataTable)
        table.display = True
        table.clear()
        for page in pages:
            self._append_page_row(table, page)
        self._update_status()

    def append_pages(self, pages: list[PageContext]) -> None:
        """Append additional pages to the existing table."""
        table = self.query_one("#page-table", DataTable)
        for page in pages:
            self._pages.append(page)
            self._append_page_row(table, page)
        self._update_status()

    def _append_page_row(self, table: DataTable, page: PageContext) -> None:
        preview = page.full_text[:120].replace("\n", " ") if page.full_text else "(empty page)"
        hit = self.HIT_MARKER if page.page_number in self._hit_pages else ""
        table.add_row(hit, str(page.page_number), preview)

    def _update_status(self) -> None:
        hit_count = sum(1 for p in self._pages if p.page_number in self._hit_pages)
        status = self.query_one("#page-status", Label)
        hit_info = f"  ({hit_count} hits)" if hit_count else ""
        status.update(f" {len(self._pages)} pages loaded{hit_info}")

    def get_pages(self) -> list[PageContext]:
        """Return all loaded pages."""
        return list(self._pages)

    def move_cursor_to_page(self, page_number: int) -> None:
        """Move the table cursor to the row matching the given page number."""
        for idx, page in enumerate(self._pages):
            if page.page_number == page_number:
                table = self.query_one("#page-table", DataTable)
                table.move_cursor(row=idx)
                return

    def show_loading(self) -> None:
        """Show loading state with animated indicator."""
        self.query_one("#page-table", DataTable).display = False
        self.query_one("#page-loading").display = True
        status = self.query_one("#page-status", Label)
        status.update(" Loading pages...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        self.query_one("#page-loading").display = False
        self.query_one("#page-table", DataTable).display = True
        status = self.query_one("#page-status", Label)
        status.update(f" Error: {message}")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if idx is not None and len(self._pages) - idx <= self.AUTOLOAD_THRESHOLD:
            self.post_message(self.NearEnd())

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._pages):
            self.post_message(self.Selected(page=self._pages[idx], all_pages=self._pages))
