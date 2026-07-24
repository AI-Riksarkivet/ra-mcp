# MCP Tools

MCP tool and resource registrations exposed by the ra-mcp server. Each `*-mcp`
package defines a `register_*` function invoked from its `tools.py`. For
end-user parameter documentation see the [Tools reference](../tools/tools.md).

## Search Tools

Source: [`packages/mcps/search-mcp/src/ra_mcp_search_mcp/search_tool.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/search-mcp/src/ra_mcp_search_mcp/search_tool.py)

Registers `search_transcribed` (full-text over AI-transcribed pages; implicit
AND between terms, wildcards/fuzzy/phrases, no boolean operators) and
`search_metadata` (titles, names, places). Results are rendered by
the package `PlainTextFormatter`
([`formatter.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/search-mcp/src/ra_mcp_search_mcp/formatter.py)).

## Browse Tool

Source: [`packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/browse_tool.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/browse_tool.py)

Registers `browse_document` (full page transcriptions by reference code), also
rendered by a package
[`PlainTextFormatter`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/formatter.py).

## Guide Resources

Source: [`packages/mcps/guide-mcp/src/ra_mcp_guide_mcp/tools.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/guide-mcp/src/ra_mcp_guide_mcp/tools.py)

Exposes the historical guides under `resources/` as MCP resources
(`riksarkivet://...`).

## HTR Tools

Source: [`packages/mcps/htr-mcp/src/ra_mcp_htr_mcp/tools.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/htr-mcp/src/ra_mcp_htr_mcp/tools.py)

Registers `htr_transcribe`, which runs handwritten text recognition (HTRflow)
over image URLs and returns per-page transcriptions plus ALTO/PAGE/JSON exports.

## Viewer Tools

Source: [`packages/mcps/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/mcps/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py)

Registers the interactive document viewer MCP App (`view_document`,
`view_manifest`, `view_bild`) with zoomable images and ALTO text-layer overlays.

## PDF Tools

Provided by `ra-mcp-pdf-mcp` (module `ra_mcp_pdf_mcp.tools`). Registers an MCP App PDF
viewer plus `display_pdf`, `search_pdf`, `list_pdfs`, `read_pdf_page`, and the app-control
tools (`pdf_go_to_page`, `pdf_set_search`, `get_pdf_state`, `get_page_blocks`,
`read_pdf_bytes`, `search_guides`). See the [Tools reference](../tools/tools.md#display_pdf)
for parameters.

## Label Studio Tools

Provided by the optional `ra-mcp-label-mcp` (module `ra_mcp_label_mcp.tools`). Registers
`import_to_label_studio`, which imports document pages and ALTO transcriptions into a Label
Studio project for human annotation.

## Dataset Tools

The optional dataset modules each register namespaced search tools over local LanceDB tables:
`diplomatics`, `sbl`, `sjomanshus`, `filmcensur`, `rosenberg`, `court`, `aktiebolag`,
`faltjagare`, `suffrage`, `specialsok`, `dds`, `wincars`, `sj`, and `tora`. The full tool list
and coverage figures are in the [Tools reference](../tools/tools.md#dataset-tools) and
[Data Sources](../how-it-works/data-sources.md#local-lancedb-datasets).
