---
name: pdf-guide
description: Guide for the PDF viewer tools. Use when the user asks to "show PDF", "open PDF", "search in PDF", "list PDFs", "visa PDF", "medeltid guide", "hur riket styrdes", "samisk historia", or wants to read/search Riksarkivet's PDF guides. Also use when deciding between view_document (archival pages) vs display_pdf (full PDF documents).
---

# Riksarkivet PDF Guides — Research Index

Three archival guides with structured text, searchable across 548 pages.

## Tools

| Tool | Purpose |
|------|---------|
| `search_guides` | Search ALL 3 guides at once — no display_pdf needed |
| `display_pdf` | Open a guide in the viewer |
| `read_pdf_page` | Read full text of a page |
| `search_pdf` | Search within one open guide (with bbox highlights) |
| `pdf_go_to_page` | Navigate viewer to a page |
| `pdf_set_search` | Highlight a term in the viewer |

## Workflow

**For topical questions** ("tell me about medieval taxation"):
1. Check the index below → find relevant section + page
2. `display_pdf(url)` → open the guide
3. `read_pdf_page(url, page)` → read the content
4. Answer with citation → `pdf_go_to_page` + `pdf_set_search` → show source

**For entity/keyword questions** ("what about Gustav Vasa?"):
1. `search_guides(term="Gustav Vasa")` → finds matches across all guides
2. Pick best matches → `display_pdf` → `read_pdf_page` → answer with citations

**Always:** cite page numbers, navigate viewer to source, let user verify.

---

## Guide 1: Medeltidens samhalle (258 sidor)

Peter Stahl. Medieval Sweden 1100-1520. Riksarkivet's medieval collections.
`url: ...216090389-e30a88-medeltidens-samhalle.pdf?download=true`

| Pages | Section | Covers |
|-------|---------|--------|
| 7-8 | Inledning | Overview of Riksarkivet's medieval collections |
| 9-20 | **Territoriella forhallanden** | Rikets granser, lagsagor, harad, socken, landskapen, landskapslagar, landslag, stadslag |
| 21-59 | **Kung, riksforestandare och rad** | Kungaval, Mora sten, eriksgata, ledung, kungen som domare, jarlsambetet, drots/marsk/kansler, riksradet, herredagar, riksmoten, riksforestandare (Sten Sture), borgar, lan, forvaltning, skattevasen, statshandlingar |
| 60-81 | **Bonder och vardsligt fralse** | Bonden i byn, storgardar, agrarkris, vardsliga fralset, jordnaturer, jordvardering, jordtransaktioner (omfard, skotning, skaftfard), testamenten |
| 82-100 | **Stader och borgerskap** | Stadernas framvaxt, stadslagar, stadsprivilegier, Hansan, immigration, handel, stadens ambetsman, topografi, dominikaner, franciskaner |
| 101-140 | **Kyrkan** | Organisation, kanonisk ratt, provinsialkoncilier, stiftssynoder, biskop, prost, domkyrkorna, sockenkyrkorna, kloster, korstagen, Birgittinorden, Vadstena kloster |
| 141-165 | **Pavedomet och pavliga brev** | Pavedomet, romerska kurian, kansliet, kammaren, rota, penitentiarian, brevtyper (bulla, breve, supplik), bullor till Sverige, legater, nuntier, Vatikanarkivet |
| 166-181 | **Medeltidsbreven** | Tradering, forvaring, slottsbranden 1697, kallutgivning 1800-talet, Svenskt Diplomatarium, SDHK |
| 182-201 | **Diplomatik, skrift, formelsprak** | Diplomatikens terminologi, brevets delar (protokoll, text, eskatokoll), datering (romersk, kyrklig), notarier, skrivmaterial, skriftens utveckling, sigill, forfalskningar |
| 202-216 | **Riksarkivets medeltidskallor** | Pergamentsbrevsamlingen, Pappersbrevsamlingen, Sturearkivet, kopiebocker, kammararkivet, alla samlingar |
| 217-238 | Ordforklaringar + Register | Glossary of medieval terms, name/subject index |

## Guide 2: Hur riket styrdes (255 sidor)

Bjorn Asker. Swedish governance, politics and archives 1520-1920.
`url: ...Hur%20riket%20styrdes_63MB.pdf?download=true`

| Pages | Section | Covers |
|-------|---------|--------|
| 13-25 | **Forvaltning, politik och arkiv** | Nyckelbegrepp (politik, stat, rike), historisk forskning |
| 26-40 | **Riket och provinserna** | Medeltidens stat, hertigdomen, stormaktsvaldet, konglomeratstaten, krympande rike |
| 41-78 | **Kungen, regeringen, riksdagen** | Grundlagar, kungaeder, regerings former, tronfolj, riksdagsordningar, tryckfrihet, formyndarregeringar, riksradet, partier, riksdagens verk |
| 79-100 | **Kansliet, ambetsverken, kommitteerna** | Kungl. Maj:ts kansli, justitiekanslern, utrikesrepresentationen, centrala ambetsverk, byrakraterna, kommitteer |
| 101-120 | **Lanen, fogderierna, staderna** | Fogdar, stathallare, lansstyrelser, landshövdingar, fogderier, fögderireformen 1918, stader |
| 121-142 | **Bergsstaten och tullen** | Bergsstat, tullforvaltning, sjotull, granstull, landtull |
| 143-159 | **Domstolarna och fangvarden** | Underratter, overratter, hovratter, hogsta domstolen, regeringsratten, fangvard |
| 160-187 | **Kyrkan, skolan, sjukvarden** | Kyrkan som statlig institution, skolvasende, sjukvard |
| 188-209 | **Krigsmakten** | Armen, flottan, militar forvaltning |
| 210-222 | **Naringarna, kommunikationer, socialpolitik** | Naringsstatsorgan, kommunikationer, pensioner, arbetarskydd |
| 223-233 | **Kommuner och landsting** | Primärkommuner, landsting, polis |
| 234-255 | **Hur riket styrdes** (sammanfattning) | Statsforvaltning och samhalle, byrakraternas varld, rangordningar, Sverige i Europa |

## Guide 3: Ingang till samisk historia (35 sidor)

Guide to Sami history in Riksarkivet's collections (2024).
`url: ...164624875-f258a1-Ingang-till-samisk-historia_2024.pdf?download=true`

| Section | Covers |
|---------|--------|
| Begrepp | Terminology (same, lapp, nomad) |
| Digitala kallor | Riksarkivets forskarsal, Ajtte, Nuohtti.com |
| Samerna och nationsgranserna | Granser, kallor om granser |
| Central forvaltning | Statlig forvaltning, kallor |
| Kommitteer och utredningar | 1882 ars lappkommitte |
| Lokal och regional forvaltning | Lanshistoria, lappfogdar, lappvasendet, domstolar, Vasterbotten, Norrbotten, Jamtland, avvittringsratten |
| Kyrkan | Lappforsamlingarna |
| Utbildning | Samisk utbildningshistoria |
| Enskilda arkiv skapade av samer | Soktips i NAD |
| Institutioner | Arkiv, museer, kulturcentra i Norden |

---

## Example Queries → Actions

| User asks | Model does |
|-----------|------------|
| "Beratta om medeltida Sverige" | Read skill TOC → Medeltidens samhalle, Inledning p.7 → display_pdf + read_pdf_page |
| "Hur fungerade kungamakten?" | TOC → Kung, riksforestandare p.21 → display_pdf + read_pdf_page(21-33) |
| "Vad sager guiderna om Gustav Vasa?" | search_guides("Gustav Vasa") → read best matches → cite |
| "Hur styrdes Sverige pa 1700-talet?" | TOC → Hur riket styrdes, kap 3-4 → display_pdf + read_pdf_page |
| "Finns det kallor om samer?" | TOC → Samisk historia → display_pdf + read sections |
| "Vad ar en bulla?" | TOC → Pavedomet p.141, brevtyper p.149 → read_pdf_page(149) |
| "Tell me about Vadstena kloster" | search_guides("Vadstena") + TOC → Kyrkan p.123 → read + cite |
| "Vad ar SDHK?" | TOC → Medeltidsbreven p.180 → read_pdf_page(180) |

---

## PDF tools vs Document Viewer

- `display_pdf` = these 3 guide publications (full PDF books)
- `view_document` = individual archival pages from Riksarkivet (IIIF images + ALTO XML transcriptions)
