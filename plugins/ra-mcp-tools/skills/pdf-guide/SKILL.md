---
name: pdf-guide
description: Guide for the PDF viewer tools. Use when the user asks to "show PDF", "open PDF", "search in PDF", "list PDFs", "visa PDF", "medeltid guide", "slaktforskning guide", or wants to read/search Riksarkivet's PDF publications. Also use when deciding between view_document (archival pages) vs display_pdf (full PDF documents).
---

# PDF Viewer — Riksarkivet's Archival Guides

## Available Guides

### Medeltidens samhalle (258 sidor)
Peter Stahl. Riksarkivets medeltidssamlingar, kallor 1100-1520.

- p.7: Inledning
- p.9: **Territoriella och judiciella forhallanden** (1100-1520)
  - p.9: Rikets granser | p.10: Lagsaga, harad, socken | p.12: Landskapen | p.15: Landskapslagar
- p.21: **Kung, riksforestandare och rad**
  - p.21: Kungaval, eriksgata, ledung | p.23: Kungen som domare | p.25: Jarlsambetet | p.26: Drots, marsk, kansler | p.29: Rikets rad | p.31: Herredagar | p.33: Riksforestandare | p.35: Borgar, lan, forvaltning | p.44: Skattevasen | p.47: Statshandlingar
- p.60: **Bonder och vardsligt fralse**
  - p.60: Bonden i byn | p.63: Storgardar, agrarkris | p.65: Vardsliga fralset | p.67: Jordnaturer | p.68: Jordtransaktioner | p.72: Testamenten
- p.82: **Stader och borgerskap**
  - p.82: Staderna vaxer fram | p.84: Stadslagar | p.86: Hansan | p.87: Stadens invanare | p.91: Topografi | p.96: Stadernas kallor
- p.101: **Kyrkan**
  - p.101: Organisation | p.104: Kanonisk ratt | p.110: Biskop, prost | p.112: Domkyrkorna | p.116: Sockenkyrkorna | p.119: Kloster | p.122: Korstagen | p.123: Birgittinorden, Vadstena
- p.141: **Pavedovet och pavliga brev**
  - p.141: Pavedovet | p.145: Romerska kurian | p.149: Brevtyper | p.152: Bullor till Sverige | p.155: Legater | p.158: Vatikanarkivet
- p.166: **Medeltidsbreven — arkivhistorisk oversikt**
  - p.166: Tradering | p.169: Forvaring 1530-1690 | p.173: Slottsbranden 1697 | p.177: Kallutgivning | p.180: SDHK
- p.182: **Diplomatik, skrift och formelsprak**
  - p.182: Terminologi | p.186: Datering | p.187: Notarier | p.189: Skriftens utveckling | p.193: Sigill | p.195: Forfalskningar
- p.202: **Riksarkivets medeltidskallor** — huvudbestand
- p.217: Ordforklaringar | p.239: Register

### Hur riket styrdes (255 sidor)
Bjorn Asker. Forvaltning, politik och arkiv 1520-1920.

### Ingang till samisk historia (2024)
Guide till samisk historia i Riksarkivets samlingar.

---

## Tools

| Tool | Purpose |
|------|---------|
| `display_pdf` | **CALL FIRST** — opens PDF in viewer |
| `search_pdf` | Search ALL pages, returns matches + text snippets |
| `read_pdf_page` | Read full text of a specific page |
| `pdf_go_to_page` | Navigate viewer to a page |
| `pdf_set_search` | Highlight a term in the viewer |
| `list_pdfs` | List available guides with URLs |

---

## Workflow

### Research with citations:
1. User asks about a topic → check TOC above for relevant section
2. Call `display_pdf` with the guide URL
3. Call `read_pdf_page` for the relevant pages
4. Answer with citations: *"Enligt Medeltidens samhalle (s. 44)..."*
5. Call `pdf_go_to_page` + `pdf_set_search` → viewer shows the source
6. For deeper search: `search_pdf` to find all mentions across pages

### Key principle:
**Always cite page numbers. Always navigate the viewer to show the source. The user must be able to verify every claim.**

---

## URLs

```
Medeltidens samhalle: https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true
Hur riket styrdes:    https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/Hur%20riket%20styrdes_63MB.pdf?download=true
Samisk historia:      https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/164624875-f258a1-Ingang-till-samisk-historia_2024.pdf?download=true
```

---

## When to use PDF tools vs Document Viewer

- `display_pdf` = full PDF books/guides (these 3 publications)
- `view_document` = individual archival pages (IIIF images + ALTO XML)
