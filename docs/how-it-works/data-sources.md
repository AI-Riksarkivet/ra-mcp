# Data Sources & Coverage

ra-mcp draws on two kinds of data sources: **live Riksarkivet HTTP APIs** (the core search/browse/viewer tools) and **local LanceDB datasets** that ship with the optional dataset modules.

## Live HTTP APIs

The core modules connect to several Riksarkivet APIs:

| API | Endpoint | Purpose |
|-----|----------|---------|
| **Search API** | `data.riksarkivet.se/api/records` | Full-text search across transcribed documents |
| **ALTO XML** | `sok.riksarkivet.se/dokument/alto` | Structured page transcriptions with text coordinates |
| **IIIF** | `lbiiif.riksarkivet.se` | High-resolution document images and collection manifests |
| **OAI-PMH** | `oai-pmh.riksarkivet.se/OAI` | Document metadata and collection structure |
| **Bildvisaren** | `sok.riksarkivet.se/bildvisning` | Interactive image viewer (links provided in results) |
| **TORA SPARQL** (`tora` module) | `tora.entryscape.net/store/sparql` | Geocode historical places — 51K settlements with WGS84 coordinates (`search_tora`) |

Most of this data comes from the [Riksarkivet Data Platform](https://github.com/Riksarkivet/dataplattform/wiki), which hosts AI-transcribed materials from the Swedish National Archives. HTR re-transcription is delegated to the [HTRflow](https://pypi.org/project/htrflow/) Gradio Space.

Additional resources: [Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm) (semantic search, experimental).

## Local LanceDB datasets

The optional dataset modules query **local LanceDB tables** rather than a live API — they are full-text/vector indexes bundled with the dataset packages. They load only when `lancedb` is installed, and each adds its own namespaced search tools (see [Module System](architecture.md#module-system)). Scale figures below are reported by the modules themselves.

| Dataset (module) | Coverage | Tools |
|------------------|----------|-------|
| **SDHK + MPO** (`diplomatics`) | 44,000+ medieval charters; 23,000+ parchment fragments | `search_sdhk`, `search_mpo`, `view_sdhk`, `view_mpo` |
| **SBL** (`sbl`) | 9,400+ biographical articles (Svenskt biografiskt lexikon) | `search_sbl`, `view_sbl_article`, `load_sbl_article` |
| **Sjömanshus** (`sjomanshus`) | 688,000+ seamen's records (voyages, registrations), 1700s–1900s | `search_liggare`, `search_matrikel` |
| **Filmcensur** (`filmcensur`) | 60,000 film censorship records, 1911–2011 | `search_filmreg` |
| **Rosenberg** (`rosenberg`) | 66,000 historical places (geographical lexicon) | `search_rosenberg` |
| **Court records** (`court`) | Domboksregister (Västra härad 1611–1730), Medelstad (1668–1750) | `search_domboksregister`, `search_medelstad` |
| **Aktiebolag** (`aktiebolag`) | Joint-stock companies 1901–1935 (~12.5K companies, ~49K board members) | `search_bolag`, `search_styrelse` |
| **Fältjägare** (`faltjagare`) | Jämtland field regiment soldiers 1645–1901 (~43K) | `search_faltjagare` |
| **Suffrage** (`suffrage`) | Women's suffrage records (Rösträtt petition 1913–1914, FKPR 1911–1920) | `search_rostratt`, `search_fkpr` |
| **Specialsök** (`specialsok`) | Flygvapen, fångrullor, kurhuset, press, video datasets | `search_flygvapen`, `search_fangrullor`, `search_kurhuset`, `search_press`, `search_video` |
| **DDS church records** (`dds`) | ~2.5M births, deaths, marriages (1600s–1900s) | `search_fodelse`, `search_doda`, `search_vigsel` |
| **Wincars** (`wincars`) | Norrland vehicle registrations 1916–1972 (~1.5M across 5 counties) | `search_wincars` |
| **SJ railway** (`sj`) | Properties (198K JUDA) and technical drawings (118K FIRA/SIRA) | `search_juda`, `search_ritningar` |

In addition, the optional `label` module is not a dataset but an integration that imports pages to a Label Studio instance for human annotation (`import_to_label_studio`).

---

## Archive Coverage

The archive has three access tiers — not all materials are searchable the same way:

| Tier | Tool | Coverage |
|------|------|----------|
| **Metadata catalog** | `search_metadata` | 2M+ records — titles, names, places, dates |
| **Digitised images** | `browse_document` (links) | ~73M pages viewable via bildvisaren |
| **AI-transcribed text** | `search_transcribed` | ~1.6M pages — currently court records (hovrätt, trolldomskommissionen, poliskammare, magistrat) from 17th-18th centuries |

Church records, estate inventories, and military records are typically cataloged and often digitised, but NOT AI-transcribed.

## Transcription Quality

The AI-transcribed text was produced by HTR (Handwritten Text Recognition) and OCR models. These transcriptions are **not perfect** — they contain recognition errors including misread characters, merged or split words, and garbled passages, especially in older or damaged documents.

This has a direct impact on search: an exact search for `Stockholm` will miss documents where the transcription reads `Stockholn` or `Stookholm` due to recognition errors. **Always use fuzzy search (`~`)** to compensate — `stockholm~1` catches common misreads and significantly increases the number of hits.

## The Plugin Model

ra-mcp is one piece of a larger ecosystem. Multiple MCP servers can be connected to the same AI client:

``` mermaid
graph LR
  client["AI Client\n(Claude)"]
  client --> ramcp["ra-mcp\nSearch, browse, HTR, viewer, PDF,\nguides, dataset modules"]
  client --> htrflow["htrflow-mcp\nStandalone HTR\n(alternative)"]
  client --> other["other servers\nAny MCP-compatible tool"]
```

Together with external tools, they enable a complete research workflow: search the archives, read transcriptions, re-transcribe pages that need better OCR/HTR, and view original documents — all from within a single AI conversation.
