---
name: pdf-guide
description: Guide for the PDF viewer tools. Use when the user asks to "show PDF", "open PDF", "search in PDF", "list PDFs", "visa PDF", "medeltid guide", "hur riket styrdes", "samisk historia", or wants to read/search Riksarkivet's PDF guides. Also use when deciding between view_document (archival pages) vs display_pdf (full PDF documents).
---

# Riksarkivet PDF Guides — Research Index

Three archival guides, 548 pages total. All searchable, all with structured text.

## Tools

| Tool | Purpose | Needs display_pdf? |
|------|---------|-------------------|
| `search_guides(term)` | Search ALL 3 guides at once | No |
| `read_pdf_page(url, page, count)` | Read 1-5 pages of text (count=3 reads page and 2 adjacent) | No |
| `display_pdf(url, title)` | Open guide in interactive viewer | — |
| `search_pdf(url, term)` | Search one guide with bbox highlights in viewer | Yes |
| `pdf_go_to_page(page)` | Navigate viewer to page | Yes |
| `pdf_set_search(search_term)` | Highlight term in viewer | Yes |

## Research Workflow

**Topical question** ("tell me about medieval taxation"):
1. Check index below → Medeltidens samhälle, Skatteväsen p.44
2. `read_pdf_page(url, page=44, count=3)` → read pages 44-46
3. Answer with citations: *"Enligt Medeltidens samhälle (s. 44)..."*
4. `display_pdf(url)` → `pdf_go_to_page(44)` → `pdf_set_search("skatt")` → user sees source

**Entity search** ("what about Gustav Vasa?"):
1. `search_guides(term="Gustav Vasa")` → matches across all guides with snippets
2. `read_pdf_page(url, page=46, count=2)` → read full context
3. Answer with citations → navigate viewer to source

**Open-ended** ("tell me about this guide"):
1. Check index below → read Inledning pages
2. Summarize the guide's scope and structure from the index

**Rules:**
- Always cite page numbers
- Always navigate the viewer to show the source after answering
- Use `count` parameter to read adjacent pages for full context
- `read_pdf_page` and `search_guides` work WITHOUT `display_pdf` — use them for research first, open viewer for showing sources

---

## Guide 1: Medeltidens samhälle (258 pages)

Peter Ståhl. Medieval Sweden 1100–1520. Riksarkivet's medieval collections.

```
URL: https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true
```

| Pages | Section | Topics |
|-------|---------|--------|
| 7–8 | Inledning | Riksarkivets medeltidssamlingar, guidens upplägg |
| 9–20 | **Territoriella förhållanden** | Rikets gränser, lagsagor, härad, socken, landskapen, landskapslagar, landslag, stadslag |
| 21–59 | **Kung, riksföreståndare och råd** | Kungaval (Mora sten), eriksgata, ledung, kungen som domare, jarlämbetet, drots/marsk/kansler, riksrådet, herredagar, riksmöten, riksföreståndare (Sten Sture), borgar, län, förvaltning (Folkgungatiden, Mecklenburgska perioden, senmedeltiden), skatteväsen, statshandlingar |
| 60–81 | **Bönder och världsligt frälse** | Bonden i byn, storgårdar, agrarkris, världsliga frälset, jordnaturer, jordvärdering, jordtransaktioner (omfärd, skötning, skaftfärd), testamenten |
| 82–100 | **Städer och borgerskap** | Stadernas framväxt, stadslagar, stadsprivilegier, Hansan, immigration, handel, stadens ämbetsmän, topografi, bränder, dominikaner, franciskaner |
| 101–140 | **Kyrkan** | Organisation, kanonisk rätt, provinsialkoncilier, stiftssynoder, biskop/prost, domkyrkorna, sockenkyrkorna, kloster, korstågen, Birgittinorden, Vadstena kloster |
| 141–165 | **Påvedömet och påvliga brev** | Påvedömet, romerska kurian (kansliet, kammaren, rota, penitentiarian), brevtyper (bulla, breve, supplik), bullor till Sverige, legater, nuntier, Vatikanarkivet |
| 166–181 | **Medeltidsbreven** | Tradering, förvaring, slottsbranden 1697, källutgivning 1800-talet, Svenskt Diplomatarium, SDHK |
| 182–201 | **Diplomatik, skrift, formelspråk** | Terminologi, brevets delar, datering (romersk, kyrklig), notarier, skrivmaterial, skriftens utveckling 1100–1520, sigill, förfalskningar |
| 202–216 | **Riksarkivets medeltidskällor** | Pergamentsbrevsamlingen, Pappersbrevsamlingen, Sturearkivet, kopieböcker, kammararkivet |
| 217–238 | Ordförklaringar + Register | Medeltida termer (avlat, birkarlar, biltog...), person/sakregister |

## Guide 2: Hur riket styrdes (255 pages)

Björn Asker. Swedish governance, politics and archives 1520–1920.

```
URL: https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/Hur%20riket%20styrdes_63MB.pdf?download=true
```

| Pages | Section | Topics |
|-------|---------|--------|
| 13–25 | **Förvaltning, politik och arkiv** | Nyckelbegrepp, historisk forskning |
| 26–40 | **Riket och provinserna** | Medeltidens stat, hertigdömen, stormaktsväldet, konglomeratstaten |
| 41–78 | **Kungen, regeringen, riksdagen** | Grundlagar, kungaeder, regeringsformer, tronföljd, riksdagsordningar, tryckfrihet, förmyndarregeringar, riksrådet, partier |
| 79–100 | **Kansliet, ämbetsverken, kommittéerna** | Kungl. Maj:ts kansli, justitiekanslern, utrikesrepresentationen, centrala ämbetsverk, byråkraterna |
| 101–120 | **Länen, fögderierna, städerna** | Fogdar, ståthållare, länsstyrelser, landshövdingar, fögderireformen 1918 |
| 121–142 | **Bergsstaten och tullen** | Bergsstat, tullförvaltning, sjötull, gränstull, landtull |
| 143–159 | **Domstolarna och fångvården** | Underrätter, överrätter, hovrätter, Högsta domstolen, regeringsrätten |
| 160–187 | **Kyrkan, skolan, sjukvården** | Kyrkan som statlig institution, skolväsende, sjukvård |
| 188–209 | **Krigsmakten** | Armén, flottan, militär förvaltning |
| 210–222 | **Näringar, kommunikationer, socialpolitik** | Näringsstatsorgan, kommunikationer, pensioner, arbetarskydd |
| 223–233 | **Kommuner och landsting** | Primärkommuner, landsting, polis |
| 234–255 | **Hur riket styrdes** (sammanfattning) | Statsförvaltning och samhälle, rangordningar, Sverige i Europa |

## Guide 3: Ingång till samisk historia (35 pages)

Guide to Sami history in Riksarkivet's collections (2024).

```
URL: https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/164624875-f258a1-Ingang-till-samisk-historia_2024.pdf?download=true
```

| Section | Topics |
|---------|--------|
| Begrepp | Terminologi (same, lapp, nomad) |
| Digitala källor | Riksarkivets forskarsal, Ájtte, Nuohtti.com |
| Samerna och nationsgränserna | Gränser, källmaterial |
| Central förvaltning | Statlig förvaltning, källor |
| Kommittéer och utredningar | 1882 års lappkommitté |
| Lokal och regional förvaltning | Länshistoria, lappfogdar, lappväsendet, domstolar, Västerbotten, Norrbotten, Jämtland, avvittringsrätten |
| Kyrkan | Lappförsamlingarna |
| Utbildning | Samisk utbildningshistoria |
| Enskilda arkiv skapade av samer | Söktips i NAD |
| Institutioner | Arkiv, muséer, kulturcentra i Norden |

---

## Example Queries → Actions

| User asks | Model does |
|-----------|------------|
| "Berätta om medeltida Sverige" | TOC → Medeltidens samhälle p.7 → `read_pdf_page(url, 7, 2)` → summarize |
| "Hur fungerade kungamakten?" | TOC → p.21-59 → `read_pdf_page(url, 21, 5)` then `read_pdf_page(url, 26, 5)` |
| "Vad säger guiderna om Gustav Vasa?" | `search_guides("Gustav Vasa")` → read best pages → cite |
| "Hur styrdes Sverige på 1700-talet?" | TOC → Hur riket styrdes p.41-78 → `read_pdf_page(url, 41, 5)` |
| "Finns det källor om samer?" | TOC → Samisk historia → `display_pdf(url)` → read sections |
| "Vad är en bulla?" | TOC → Påvedömet p.149 → `read_pdf_page(url, 149, 2)` |
| "Tell me about Vadstena kloster" | `search_guides("Vadstena")` + TOC → p.123 → `read_pdf_page(url, 123, 3)` |
| "Vad är SDHK?" | TOC → Medeltidsbreven p.180 → `read_pdf_page(url, 180, 2)` |

---

## PDF tools vs Document Viewer

- `display_pdf` = these 3 guide publications (full PDF books)
- `view_document` = individual archival pages from Riksarkivet (IIIF images + ALTO XML transcriptions)
