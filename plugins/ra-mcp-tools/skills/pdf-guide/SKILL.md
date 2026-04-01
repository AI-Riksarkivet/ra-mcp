---
name: pdf-guide
description: Searches and reads Riksarkivet's archival PDF guides (medieval Sweden, governance 1520-1920, Sami history). Use when user asks about Swedish history, archives, medieval charters, governance, Sami, or wants to open/search PDF guides. Provides section-level references with page numbers for citation.
---

# Riksarkivet PDF Guides

Three guides, 548 pages. Structured text with page-level access.

## Tools

| Tool | Needs display_pdf? | Purpose |
|------|-------------------|---------|
| `search_guides(term)` | No | Search ALL guides at once |
| `read_pdf_page(url, page, count)` | No | Read 1–5 pages of text |
| `display_pdf(url)` | — | Open viewer |
| `pdf_go_to_page(page)` | Yes | Navigate viewer |
| `pdf_set_search(term)` | Yes | Highlight in viewer |
| `search_pdf(url, term)` | Yes | Search one guide with highlights |

## Workflow

1. Check reference files below → find section + pages
2. `read_pdf_page(url, page, count)` → read content
3. `display_pdf(url)` → open viewer (BEFORE go_to_page/set_search)
4. Answer with page citations
5. `pdf_go_to_page` + `pdf_set_search` → show source

For entity searches: `search_guides(term)` → read matches → cite → show in viewer.

## Guides

### Medeltidens samhälle (258 pages, 1100–1520)
Detailed sections: [medeltid.md](medeltid.md)

| Pages | Topic |
|-------|-------|
| 9–20 | Territories, härad, socken, landskapslagar |
| 21–59 | **Kungamakt**: kungaval, eriksgata, jarlar, drots/marsk, riksråd, herredagar, Sturetiden, borgar/län, skatter, statshandlingar |
| 60–81 | **Bönder/frälse**: jordnaturer, jordtransaktioner, testamenten, Alsnö stadga |
| 82–100 | **Städer**: stadslagar, Hansan, stadsförvaltning |
| 101–140 | **Kyrkan**: stift, domkyrkorna, kloster, Vadstena, korståg |
| 141–165 | **Påvedömet**: kurian, brevtyper (bulla/breve/supplik), Vatikanarkivet |
| 166–181 | **Medeltidsbreven**: tradering, slottsbranden 1697, SDHK |
| 182–201 | **Diplomatik**: skrift, datering, sigill, förfalskningar |
| 202–216 | **RA:s medeltidskällor**: alla samlingar med SE/RA-koder |

### Hur riket styrdes (255 pages, 1520–1920)
Detailed sections: [hur-riket-styrdes.md](hur-riket-styrdes.md)

| Pages | Topic |
|-------|-------|
| 26–40 | Riket: stormaktsväldet, Finland, konglomeratstat |
| 41–78 | **Kung/riksdag**: grundlagar, 1634/1719/1809 RF, tryckfrihet, ståndriksdag→tvåkammar |
| 79–100 | **Kansliet/ämbetsverk**: Oxenstierna, departementalreformen 1840, centrala verk |
| 101–120 | Län, fögderier, städer, landshövdingar |
| 121–142 | Bergsstaten, tullen |
| 143–159 | Domstolar, hovrätter, HD, fångvård |
| 160–187 | Kyrkan, skolan, sjukvården |
| 188–209 | Krigsmakten: armén, flottan, indelningsverket |
| 210–233 | Kommuner, landsting, polis, socialpolitik |

### Ingång till samisk historia (35 pages)
Detailed sections: [samisk-historia.md](samisk-historia.md)

| Section | Topic |
|---------|-------|
| Nationsgränser | Lappkodicillen 1751, renbetesrätt |
| Förvaltning | Lappfogdar, lappväsendet 1885–1971 |
| Kommittéer | 1882 lappkommittén, sanningskommissionen 2022 |
| Domstolar | Lappmarkstingslag, domböcker 1689–1750 |
| Avvittring | Skattefjäll, odlingsgränsen |
| Kyrkan | Lappförsamlingar 1746–1942 |
| Utbildning | Nomadskolor, Skytteanska skolan 1632 |

## URLs

```
medeltid:  https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true
styrdes:   https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/Hur%20riket%20styrdes_63MB.pdf?download=true
samisk:    https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/164624875-f258a1-Ingang-till-samisk-historia_2024.pdf?download=true
```
