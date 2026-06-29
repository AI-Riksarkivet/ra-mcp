# MCP Tools

MCP tool and resource registrations exposed by the ra-mcp server.

## Search Tools

::: ra_mcp_search_mcp.search_tool

### Formatter

::: ra_mcp_search_mcp.formatter.PlainTextFormatter

## Browse Tool

::: ra_mcp_browse_mcp.browse_tool

### Formatter

::: ra_mcp_browse_mcp.formatter.PlainTextFormatter

## Guide Resources

::: ra_mcp_guide_mcp.tools

## HTR Tools

::: ra_mcp_htr_mcp.tools

## Viewer Tools

::: ra_mcp_viewer_mcp.tools

## PDF Tools

Provided by `ra-mcp-pdf-mcp` (module `ra_mcp_pdf_mcp.tools`). Registers an MCP App PDF
viewer plus `display_pdf`, `search_pdf`, `list_pdfs`, `read_pdf_page`, and the app-control
tools (`pdf_go_to_page`, `pdf_set_search`, `get_pdf_state`, `get_page_blocks`,
`read_pdf_bytes`, `search_guides`). See the [Tools reference](../tools/tools.md#display_pdf)
for parameters. Auto-generated docs are omitted here because the package is outside the API
autodoc paths.

## Label Studio Tools

Provided by the optional `ra-mcp-label-mcp` (module `ra_mcp_label_mcp.tools`). Registers
`import_to_label_studio`, which imports document pages and ALTO transcriptions into a Label
Studio project for human annotation.

## Dataset Tools

The optional dataset modules each register namespaced search tools over local LanceDB tables:
`diplomatics`, `sbl`, `sjomanshus`, `filmcensur`, `rosenberg`, `court`, `aktiebolag`,
`faltjagare`, `suffrage`, `specialsok`, `dds`, `wincars`, `sj`, and `tora`. The full tool list
and coverage figures are in the [Tools reference](../tools/tools.md#dataset-tools) and
[Data Sources](../how-it-works/data-sources.md#local-lancedb-datasets). Auto-generated API docs
are omitted here because these packages are optional and outside the autodoc paths.
