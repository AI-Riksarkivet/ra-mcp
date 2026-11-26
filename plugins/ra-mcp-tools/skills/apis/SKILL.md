---
name: riksarkivet-apis
description: Use when querying the Swedish National Archives (Riksarkivet) open APIs: Search API, linked data, IIIF images/manifests, OAI-PMH, TORA (Solr/SPARQL) and the EntryScape data catalog. Consider using this when making visualizations and services.
---

## Riksarkivet APIs

All of Riksarkivet's APIs provides different data or different subsets of the same data. The riches data from the core services comes for the linked data APIs while search and OAI-PMH are great for discovery.

**If a Riksarkivet MCP connector is available in the session** (tools like `search_metadata`, `search_transcribed`, `view_document`, `tora_search_tora`, `dds_search_*`), prefer those tools for interactive lookups. Use the raw APIs below for bulk work, code, SPARQL, or anything the connector does not cover.

**Network note:** sandboxed shells often cannot reach `*.riksarkivet.se` or `*.entryscape.net` (proxy 403). If curl is refused, use WebFetch for GET requests (keep URLs short; long URLs are rejected) or ask the user to allow the domains. SPARQL needs POST requests.

Always cite the reference code (`SE/…`) and the sok.riksarkivet.se link when presenting results to users. You may use the APIs as fast as you wish as long as you do not parallelize requests, always implement stand down on non-client error. To make it easier in case you need support consider using an unique User-Agent.

## Service map (hosts / URI roots)

| Purpose | Root | What lives there |
| --- | --- | --- |
| Primary data + Search API | `data.riksarkivet.se` | Archive records, agents, concepts, schema, special-search registers, `/api/records` |
| IIIF | `lbiiif.riksarkivet.se` | Images, manifests, collections, content search, annotations |
| OAI-PMH | `oai-pmh.riksarkivet.se/OAI` | EAD harvesting |
| Data catalog (EntryScape) | `katalog.riksarkivet.se/store` | DCAT-AP descriptions of Riksarkivet's datasets |
| TORA (EntryScape) | `tora.entryscape.net/store` | Historical settlement units, places, TORA schema/concepts; SPARQL |
| Web UI | `sok.riksarkivet.se` | Human-readable pages (`/arkiv/{pid}`, `/agent/{pid}`, `/topografi/{id}`) |

If you come across links pointing to  `iiif.riksarkivet.se` swap them to `lbiiif.riksarkivet.se`.

## Choosing an API

- Find records, people, organisations, places, register entries by text → **Search API** (`/api/records`).
- Full description of one record → **Linked data** (`.jsonld`).
- Images / page scans → **IIIF** (pid → collection → manifest → canvases → image service).
- Search inside AI-transcribed text → Search API `transcribed_text` (across volumes) then **IIIF Content Search** (within one volume).
- Mass harvest of archive descriptions → **OAI-PMH** (ListIdentifiers + GetRecord) or the dump at  https://riksarkivet.se/psidata/arkivmetadata.
- Historical villages/farms, coordinates, parish/county hierarchies → **TORA**: Solr search for lookups, **SPARQL** for structured or bulk queries.
- Which datasets exist and where to download them → **Data catalog** EntryScape (DCAT).

## 1. Search API — `https://data.riksarkivet.se/api/`

Methods: `/api/version`, `/api/status`, `/api/records`. Only covers material administered by Riksarkivet itself (not external institutions' data).

### `/api/records` parameters

| Kind | Param | Notes |
| --- | --- | --- |
| Query | `text` | General free text |
|  | `name` | Name search |
|  | `place` | Referenced place name |
|  | `transcribed_text` | AI-transcribed text; **requires** `only_digitised_materials=true` |
| Sort | `sort` | `relevance` (default), `alphaAsc`, `alphaDesc`, `timeAsc`, `timeDesc` |
| Paging | `offset` (default 0), `limit` (default 100) |  |
| Filter | `year_min`, `year_max` | Matches record date *and* provenance date |
|  | `only_digitised_materials=true` |  |
|  | `facet=Name:Value;Name:Value` | Combine with `;` |

Facets:

- `ObjectType`: `RecordSet` (fonds/series), `Record` (single unit), `Agent`, `Topography`, `Register`
- `Place`: hierarchical, e.g. `Sverige/Stockholms län/Stockholms kommun`
- `Type`, which depends on the ObjectType:
  - RecordSet: `Fonds`, `Series`
  - Record: `Volume`, `Dossier`, `Photography`, `MapDrawing`, `MotionPicture`, `SoundRecording`, `DigitalImage`, `DigitalFile`, `DigitalMedium`, `DigitalImageCopy`, `Microfilm`, `MicrofilmCopy`, `SearchUtility`, `Component`
  - Agent: `Person`, `Family`, `GovernmentAuthority`, `FormerGovernmentAuthority`, `Organization`, `ArchivalInstitution`, … (see wiki)
  - Topography: `Country`, `County`, `Parish`, `Municipality`, `Hundred`, `Province`, `SettlementUnit`, `ParishPart`, …
  - Register: `BirthRecord`, `MarriageRecord`, `IndexOfTitleDeedsRecord`
- `ArchivalInstitution` (e.g. `Riksarkivet i Stockholm/Täby`), `Provenance` (`GovernmentAuthority`, `MunicipalAuthority`, `Company`, `Association`, `Person`, …)

Examples:

```
https://data.riksarkivet.se/api/records?text=Nobel&limit=20
https://data.riksarkivet.se/api/records?text=stockholm&facet=ObjectType:Record;Type:MapDrawing
https://data.riksarkivet.se/api/records?transcribed_text=kaffe&only_digitised_materials=true
https://data.riksarkivet.se/api/records?text=Alskog&facet=ObjectType:Register;Type:IndexOfTitleDeedsRecord
```

### Query syntax

The `text`, `name`, `place` and `transcribed_text` parameters go to a plain free-text engine, not a full Solr/Lucene endpoint. The same rules apply to the MCP tools `search_transcribed` and `search_metadata`, which call this API.

| Syntax | Example | Meaning |
| --- | --- | --- |
| Single term | `Stockholm` | Find the word |
| Several terms | `pest smitta` | All terms required in the same document (implicit AND) |
| Wildcard | `troll*`, `st?ckholm`, `*holm` | `*` = many characters, `?` = one character |
| Fuzzy | `Stockholm~1` | Similar words within edit distance 1 (`~2` for 2) |

Not supported, never use:

- **`AND` / `OR` / `NOT` / `|` / parentheses.** There is no boolean parser, so these words are searched as literal text. `pest AND smitta` returns about 1.64M junk hits instead of the 33 documents `pest smitta` finds, or the query is rejected.
- **OR logic.** There is no syntax for it. Run one search per alternative (`troll*`, then `häx*`) and merge the results.
- **Quoted phrases on transcribed text.** They always return 0, even for a phrase that occurs verbatim on a page. Use plain multi-term search instead (`kyrka stöld` = both words anywhere in the volume). In metadata search, quotes work only for reference codes: `"SE/RA/720660"` lists an archive's volumes, while quoted title phrases return 0.
- **Proximity (`"a b"~10`).** Not honoured; returns 0 like any quoted phrase.
- **Boosting (`term^4`).** Unverified and adds nothing, so leave it out.

### Searching AI-transcribed text

All transcribed text comes from HTR/OCR models and contains misread characters, merged or split words and garbled passages, especially in old or damaged documents. **Use fuzzy search by default** on `transcribed_text`: `~1` for short words, `~2` for long words or very old documents. For stem variants use a wildcard (`troll*`).

- `stockholm~1` finds Stockholm, Stockholn, Stookholm
- `trolldom~1` finds trolldom, trolldoin, trolldorn
- `präst~1` finds präst, prast, prest

Search strategy:

1. Start with `transcribed_text` for text mentions, then use `text`, `name` or `place` to find documents by title, person or place.
2. Paginate (`offset` 0, 50, 100, …) to find more matches.
3. Search related terms one at a time (this replaces OR): historical spellings, synonyms (`satan`, then `djäfvul`), other word forms (`trolleri`, then `trollkonst`).
4. Narrow by adding terms (`pest smitta` returns only documents with both), `year_min`/`year_max`, or `sort=timeAsc` for the earliest mentions.
5. Note reference codes and page numbers, then read the pages (MCP `browse_document`, or IIIF content search and images).

Common old Swedish spellings (search both, or cover them with one wildcard or fuzzy term):

| Modern | Archaic / variant | Covered by |
| --- | --- | --- |
| präst | prest | `pr?st` or `präst~1` |
| silver | silfver, silfv | `sil*er` or `silf*` |
| guld | gull | `gul*` |
| kyrka | kyrcka, kyrck | `kyrk*` or `kyrck*` |
| kvinna | qvinna, qwinna | `q*inna` or `kvinna~1` |
| stöld | tiufnad, tjufnad | separate searches |
| häxa | hexa | `h?xa` |
| trolldom | trulldom | `tr?lldom` |
| djävul | djäfvul, diefvul | `dj?f*` plus separate searches |

General letter drift: ä↔æ/e, ö↔ø/o, v↔f/fv/w, k↔ck/c. `?` and `~1` absorb most of it.

### Response (JSON)

- `totalHits`, `hits`, `offset`
- `facets[]`: `{name, values[{value, hits, url, subFacets?}]}`. Each `url` re-runs the search filtered on that value, so follow it rather than building facet strings by hand.
- `items[]`: `id` (pid; base62 UUID for records/agents, numeric id for topographies), `objectType`, `type`, `caption`, `metadata`, `_links`
  - `metadata` for records: `referenceCode` (e.g. `SE/ULA/10012/A 1/1`), `hierarchy[]`, `provenance[]`, `archivalInstitution[]` (each `{caption, uri, date}`), `date` (**free text, not normalised**), `note`
  - Registers: BirthRecord `date, childsName, fathersName, mothersName, parish`; MarriageRecord `groomsName, bridesName, parish, date`; IndexOfTitleDeedsRecord `parish, propertyName, taxUnit, year, districtCourtSessions, paragraph`
  - `_links`: `self` (linked-data URI), `html`, `rdf/xml`, `json-ld`, `ead/ra`, `ead/ape` (records only), `image` (IIIF manifest — only present when digitised, unrestricted, openly licensed and older than 70 years)
- `_links` (top level): `self`, `next`, `previous`. Paginate by following `next` until it's absent or `offset >= totalHits`.

## 2. Linked data

| Object | URI pattern |
| --- | --- |
| Archive record (fonds/series/volume) | `http://data.riksarkivet.se/archive/{pid}` |
| Agent (person/organisation) | `http://data.riksarkivet.se/agent/{pid}` |
| Topography (TORA) | `http://data.riksarkivet.se/tora/{id}` (TORA stores these as `https://`) |
| Concept | `http://data.riksarkivet.se/concept/{property}/{value}`, e.g. `…/concept/Extent/Width` (not dereferenceable) |
| TORA concept | `https://data.riksarkivet.se/tora/{property}/{value}`, e.g. `…/tora/namingprinciple/modern` |
| TORA schema | `http://data.riksarkivet.se/tora/schema/{Class or property}`, e.g. `HistoricalSettlementUnit`, `modernParish` |
| Own schema | `http://data.riksarkivet.se/schema/` (structural only, not dereferenceable) |
| Special-search register entry | `http://data.riksarkivet.se/register/{pid}`&#32; |

Dereferencing (Cool URIs, 303 redirect by `Accept`):

- none / `text/html` → `https://sok.riksarkivet.se/{type}/{pid}`
- `application/ld+json` → `https://data.riksarkivet.se/{type}/{pid}.jsonld`

Best practice: use header-based content negoation in code and the `.jsonld` suffix when communicating with a human.&#32;

## 3. IIIF — `https://lbiiif.riksarkivet.se`

Supports Image API 3.0, Presentation 3.0, Content Search 1.0. Image ids look like `arkis``!R0001216_00005` (volume id + `_` + 5-digit page); volume/manifest ids like `arkis!R0001216`.

| Resource | Pattern |
| --- | --- |
| Manifest | `/{volume-id}/manifest` |
| Canvas | `/{image-id}/canvas` |
| Annotation page / annotation | `/{image-id}/annotationpage`, `/{image-id}/annotation` |
| Image service base | `/v3/{image-id}` (ImageService3), `/v2/{image-id}` (ImageService2) |
| Image | `/{image-id}/{region}/{size}/{rotation}/default.jpg` (also `/v3/…`, `/v2/…`) |
| Collection root | `/collection/riksarkivet`; parallel trees `/collection/amnesomraden` (topics), `/collection/tid` (century/decade/year) |
| Record as collection | `/collection/arkiv/{pid}` |
| Content search | `/search/{volume-id}?q=term` |
| Autocomplete | `/search/{volume-id}/autocomplete?q=Bro` |

Image parameters (level 1 only):

- region: `full`, `square`, `x,y,w,h` (no `pct:`)
- size: v3 `max`, `w,`, `,h`, `w,h`; no upscaling (`^`) or `!w,h`
- rotation: `0`, `90`, `180`, `270`, mirrored with `!` prefix
- quality: `default` only; format: `jpg` only

Errors: 400 bad params, 403 no rights statement / not available via API, 404 missing, 429 rate limited (read `X-RateLimit-*` headers and back off), 501 not implemented. The service often answers with misleading errors such as **500** for what are really client errors. Don't assume a server outage, check your ids first.

CORS: there is no `Access-Control-Allow-Origin: *`. Send `Origin: https://your.domain` to get it echoed back, or use a reverse proxy.

Rights: full access when the material is unrestricted, openly licensed (PDM, CC0, CC-BY) and older than 110 years. Material younger than 110 years is only reachable while logged in to sok.riksarkivet.se in the same browser.

### Workflow: pid → images

```python
import requests
B = "https://lbiiif.riksarkivet.se"

def manifests_for_pid(pid):
    col = requests.get(f"{B}/collection/arkiv/{pid}", timeout=30).json()
    return [i["id"] for i in col.get("items", []) if i["type"] == "Manifest"]

def image_urls(manifest_url, size="1200,"):
    m = requests.get(manifest_url, timeout=30).json()
    out = []
    for canvas in m["items"]:
        body = canvas["items"][0]["items"][0]["body"]
        svc = body["service"][0]
        base = svc.get("id") or svc.get("@id")
        out.append(f"{base}/full/{size}/0/default.jpg")
    return out

# e.g. pid 2Yz2ClKdn2VMeUXQcoZOO6 -> arkis!R0000480/manifest
```

For a series-level pid the collection holds manifests per volume (and same-archive "See:" cross-references). Volumes in other archives are not included. You can also get the manifest from a Search API hit's `_links.image`. Official example: https://github.com/Riksarkivet/dataplattform/blob/main/docs/examples/iiif\_presentation/pid\_to\_image\_id.py

### Workflow: transcribed text

1. `GET /api/records?transcribed_text="kaffe"&only_digitised_materials=true` to find volumes.
2. Take the volume id from `_links.image` (e.g. `arkis!40008511`).
3. `GET https://lbiiif.riksarkivet.se/search/arkis!40008511?q=kaffe` to get hits with canvas + `xywh` targets; crop with the Image API to show the snippet.

## 4. OAI-PMH — `https://oai-pmh.riksarkivet.se/OAI`

For harvesting only, with no search or sort. Responses are `text/xml`.

- `?verb=Identify`, `?verb=ListMetadataFormats` (no per-record `identifier` support)
- `?verb=ListAllAuth` lists datasets (non-standard verb)
- `/OAI/{dataset}?verb=ListIdentifiers[&from=…&until=…]` — dataset **must be in the path**, e.g. `/OAI/SE_ULA?verb=ListIdentifiers`
- `?verb=GetRecord&identifier={reference code}&metadataPrefix=oai_ape_ead|oai_ra_ead`
- **Not supported:** `ListSets`, `ListRecords`. Harvest with ListIdentifiers, then GetRecord per id.
- Identifier = reference code, e.g. `SE/ULA/10012` (fonds), `SE/ULA/10012/A 1` (series), `SE/ULA/10012/A 1/1` (volume). **Encode spaces as `+`, not `%20`:** `identifier=SE/ULA/10012/A+1`
- Formats: apeEAD (Archives Portal Europe subset of EAD2002) or RA-EAD (http://xml.ra.se/ead/RA\_EAD.xsd). Field docs in the wiki pages RA-EAD / APE-EAD.

## 5. EntryScape / EntryStore (TORA and data catalog)

TORA and the data catalog run on EntryScape (MetaSolutions), whose backend is the **EntryStore REST API** (source: https://github.com/MetaSolutionsAB/entrystore). Stores:

- TORA: `https://tora.entryscape.net/store` (UI https://tora.entryscape.net/tora/, also https://data.riksarkivet.se/tora). Known contexts: `61` (≈25.7k historical settlement units), `59` (≈4.6k), `56` (modern parishes), plus small ones (`7`, `18`).
- Data catalog: `https://katalog.riksarkivet.se/store`. DCAT datasets/distributions live in context `1`. Data is harvested by dataportal.se and data.europa.eu and are accessible through their APIs as well.

Context numbers may change, so discover them with a `context` facet (see below).

### REST URL structure

| Resource | URL |
| --- | --- |
| Entry (info + metadata + relations, JSON) | `{store}/{ctx}/entry/{id}` (add `?includeAll` for everything) |
| Metadata graph | `{store}/{ctx}/metadata/{id}` (`?format=application/ld+json` / `text/turtle` / `application/rdf+xml`, or `Accept` header) |
| Resource | `{store}/{ctx}/resource/{id}`. In the catalog this is the persistent URI of the dataset/distribution/org (e.g. `/store/1/resource/38`) |
| Relations (entries pointing here) | `{store}/{ctx}/relations/{id}` |
| Lookup by resource URI | `{store}/lookup?uri={encoded URI}` |
| Solr search | `{store}/search?type=solr&query=…` |
| SPARQL | `POST {store}/sparql` with a form-encoded body `output=json&query=…` (see SPARQL below). The TORA web UI is https://tora.entryscape.net/snorql/ |

In TORA the entry id usually equals the TORA id: `https://data.riksarkivet.se/tora/25900` → `https://tora.entryscape.net/store/61/entry/25900`. If you only have the URI, use `lookup?uri=`.

### Solr search

`GET {store}/search?type=solr&query=<solr>&limit=<n>&offset=<n>&sort=<field asc|desc>&facetFields=<f1,f2>&filterQuery=<fq1,fq2>&rdfFormat=application/ld+json`

- `query` must be at least 3 characters. Default `limit` is 50; the server caps it.
- Useful fields: `title` (n-gram, prefix-friendly, e.g. `title:Alunda`), `title.sv`, `rdfType`, `resource`, `context` (full store URL of the context), `public:true`, `modified`, `created`, `tag.literal`, `lang`, `all`/`fulltext`
- Predicate-specific fields: `metadata.predicate.{literal|literal_s|literal_t|uri|integer|date}.{md5(predicateURI)[:8]}`. Hashes for common predicates:
  - `dcterms:title` → `3f2ae919`
  - `rdfs:label` → `4f75ce12`
  - `skos:prefLabel` → `8d3b7b43`
  - compute others with `hashlib.md5(uri.encode()).hexdigest()[:8]`
  - Prefix any of these with `related.` to match on related entries.
- **Escape** `:` `/` `#` in URI values with `\`, then URL-encode, e.g. `rdfType:https\://data.riksarkivet.se/tora/schema/HistoricalSettlementUnit`
- `filterQuery` is URL-decoded twice: send `+` as `%252B` and commas inside a filter as `%252C`. Prefer `AND` over `+`.
- Response: `{results, offset, limit, facetFields[{name, valueCount, values[{name,count}]}], resource:{children[]}}`. Each child has `entryId`, `contextId`, `info`, `metadata`, `relations`, `rights`. `metadata` is RDF/JSON keyed by subject URI → predicate → `[{type, value, lang?}]`.

Examples:

```
# TORA: settlement units named like Alunda
https://tora.entryscape.net/store/search?type=solr&query=title:Alunda&limit=10
# All historical settlement units, with a context breakdown
https://tora.entryscape.net/store/search?type=solr&query=rdfType:https%5C%3A%2F%2Fdata.riksarkivet.se%2Ftora%2Fschema%2FHistoricalSettlementUnit&limit=1&facetFields=context,rdfType
# Data catalog: all DCAT datasets
https://katalog.riksarkivet.se/store/search?type=solr&query=rdfType:http%5C%3A%2F%2Fwww.w3.org%2Fns%2Fdcat%23Dataset&limit=100
```

### SPARQL (TORA)

Endpoint: `https://tora.entryscape.net/store/sparql`. Use **POST** with `Content-Type: application/x-www-form-urlencoded` and the form fields `output=json` and `query=<SPARQL>`. Send `Accept: application/sparql-results+json`. The response is standard SPARQL JSON results (`head.vars`, `results.bindings[]`). Use POST rather than GET, because queries with prefixes quickly get too long for a URL. None of the browser headers (Origin, Referer, Sec-Fetch-\*) are needed.

Prefixes the snorql UI adds (declare whichever you use; `geo:` added for coordinates):

```
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
```

curl:

```bash
curl -s https://tora.entryscape.net/store/sparql \
  -H 'Accept: application/sparql-results+json' \
  --data-urlencode 'output=json' \
  --data-urlencode 'query=PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
SELECT DISTINCT ?source WHERE { ?s a tora:CoordinateSource ; dcterms:source ?source }'
```

Python:

```python
import requests

PREFIXES = """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
"""

def tora_sparql(q):
    r = requests.post("https://tora.entryscape.net/store/sparql",
                      data={"output": "json", "query": PREFIXES + q},
                      headers={"Accept": "application/sparql-results+json"},
                      timeout=60)
    r.raise_for_status()
    return [{k: v["value"] for k, v in b.items()} for b in r.json()["results"]["bindings"]]

rows = tora_sparql("""
SELECT ?s ?label ?lat ?long WHERE {
  ?s a tora:HistoricalSettlementUnit ; skos:prefLabel ?label ;
     tora:modernParish <https://data.riksarkivet.se/tora/modernparish/191707000> .
  OPTIONAL { ?s geo:lat ?lat ; geo:long ?long }
} LIMIT 100""")
```

Useful classes to query: `tora:HistoricalSettlementUnit`, `tora:ModernParish`, `tora:TopographicalDivision`, `tora:ToraPartner`, `tora:CoordinateSource`. To look at an unfamiliar resource, run `DESCRIBE <uri>` or open `https://tora.entryscape.net/snorql/?describe=<encoded uri>`. Use `LIMIT`/`OFFSET` for large result sets.

### TORA data model (HistoricalSettlementUnit)

- Label: `skos:prefLabel` (`altLabel` for variants)
- Id: `dcterms:identifier`
- Coordinates: `geo:lat` / `geo:long` (WGS84) and `tora:sweref99_n` / `tora:sweref99_e`. **These use decimal commas (`60,1101`), so replace `,` with `.` before parsing.**
- Coordinate accuracy: `dcterms:coverage` → `…/tora/coordinateaccuracy/{high|…}`
- Administrative links: `tora:modernParish`, `modernMunicipality`, `modernCounty`, `earlyModernParish`, `earlyModernDistrict`, `earlyModernProvince`, plus `dcterms:isPartOf`
- Source partner: `dcterms:creator` → `…/tora/torapartner/{agk|dms|herr|suec|lm|isof|…}`
- Naming principle: `dcterms:conformsTo` → `…/tora/namingprinciple/modern`

Other classes include `ModernParish` (with `tora:parishcode`, `province_name`, `start_year`), `TopographicalDivision`, `ToraPartner` and `CoordinateSource`. The Search API's `Topography` objects also cover TORA (`_links.json-ld` → `https://data.riksarkivet.se/tora/{id}.jsonld`).

### Data catalog workflow

Search `rdfType` `dcat:Dataset`, read `dcterms:title` and `dcat:distribution` (URIs like `/store/1/resource/141`), then fetch each distribution's metadata via `lookup?uri=` or its entry to get `dcat:accessURL` / `dcat:downloadURL`.
