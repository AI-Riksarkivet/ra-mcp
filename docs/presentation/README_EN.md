---
title: RA-MCP in five slides (English)
owner: AI-labb och datatjänster, Riksarkivet
updated: 2026-10-15
applies to release: the autumn 2026 beta (server on Hugging Face)
---

# RA-MCP in five slides

English version of the shared deck for anyone presenting RA-MCP to a non-Swedish-speaking audience. The Swedish version (`README.md`, `RA-MCP_HT2026.pptx`) is the master; this text and `RA-MCP_HT2026_EN.pptx` follow it. When one changes, update all four files.

**At each release:** re-run the example questions on slide 3 against the new version and update the expected answers, check the modules on slide 2 and the address and limits on slides 4–5, and update the date above and in the PowerPoint file. Each slide has speaker notes of about 60 seconds.

**Tip for presenting in English:** ask the example questions in English. The assistant searches the Swedish sources and answers in English – which shows the language point on slide 1 better than any slide can.

---

## Slide 1 – What is RA-MCP?

**MCP (Model Context Protocol)** is an open standard that lets AI assistants use external tools and data sources.

**RA-MCP** turns the National Archives’ sources into such tools – ask in any language in Claude, ChatGPT or Mistral.

Diagram: **You** (ask a question in any language – English, Swedish, Finnish …) → **The AI assistant** (interprets the question, picks tools and searches in Swedish – including old spellings) → **RA-MCP** (queries our systems – the data stays with us, no copy leaves the archive) → **Our sources** (finding aids for 250,000 archives, 73 million images, transcribed handwriting and 30+ registers).

Footnote: The language skills come from the language model – the answer comes back in your language, with references to the originals.

> **Speaker notes (60 s):**
> Why does this matter? More and more people reach information through an AI assistant rather than a search interface – and that is happening whether or not archives prepare for it. We want to be where the questions are asked. MCP is an open standard that lets an AI assistant use tools outside itself. RA-MCP turns our finding aids, 73 million images, transcribed handwriting and some thirty registers into such tools. Follow the picture: you ask in whatever language you like. The assistant picks the tools and searches in Swedish, including historical spellings. The answer comes back in your language, with links to the originals. You don’t need to know which database holds the answer – or read Swedish. And importantly for an archive: the data stays with us. The assistant can ask questions, but no copy leaves the archive. The same principle could work across several institutions. And because MCP is a standard, we are not tied to one vendor – Claude, ChatGPT and Mistral all work.

---

## Slide 2 – What’s in RA-MCP?

Eight cards:
- **Search handwriting** – AI-transcribed text, including old spellings
- **Search the catalogue** – 250,000 finding aids and 2 million+ other records
- **View the originals** – page through and open the image with the text on top
- **People** – births, deaths, marriages and the biographical lexicon
- **Middle Ages** – medieval charters (SDHK, *Svenskt Diplomatariums huvudkartotek*, the main card index of Swedish medieval charters) and parchment fragments (MPO)
- **More registers** – seamen’s houses, court records, companies, vehicles etc.
- **Research guides** – the Archives’ PDF guides to sources and archival history
- **Skills** (highlighted) – built-in guidance that teaches the AI how to search archives

Footnote: Some thirty searchable sources – and the AI chooses which ones it needs for your question.

Skills in detail: eight built-in guides (`archive-search`, `archive-research`, `archival-guide`, `htr-transcription`, `view-document-guide`, `pdf-guide`, `upload-files`, `feedback-ls`).
  *For the presenter:* In Claude (claude.ai, Desktop, VS Code) skills come along automatically as MCP resources when you connect the server. In Claude Code they are installed as the `ra-mcp-tools` plugin. How ChatGPT and Mistral use them is not documented – don’t say they work there until it has been tested. `htr-transcription` and `feedback-ls` belong to features that are switched off on the open server.

> **Speaker notes (60 s):**
> This is what sits behind RA-MCP. The core is three things: searching AI-transcribed handwriting, searching the catalogue, and opening the original image with the text on top. Around that are some thirty registers – births, deaths and marriages from the church records, the Swedish Biographical Lexicon, medieval charters, seamen’s houses, court records and more. The dark card is skills. That is built-in guidance that teaches the AI how to search archives – old spellings, misread handwriting, proper citation. It is the difference between searching and searching well, and you don’t need to install anything extra. The point: you don’t need to know which source holds the answer. The AI chooses.

---

## Slide 3 – What can you ask?

Three users – only the questions are shown on the slide; the answers come in the demo. The questions were tested (in Swedish) against the release on 14 October 2026.

- **The genealogist · church records (DDS):** “What can you find about my ancestor Mathis Michaelsson in Asarum, Sweden?”
- **The researcher · transcribed handwriting:** “Can you find historical testimonies about the 1834 cholera epidemic, compare how the disease was described in different records, and show the original sources behind your conclusions?” – *Follow-up:* “What new research questions does this record raise, and what further archival material would I need to examine?”
- **The archivist · where is the material?:** “Can you find material of Sámi relevance in the National Archives’ HTR-transcribed collections?”

### Expected answers (for the presenter – not shown on the slide)

The answers will come back in English, but the sources, quotes and reference codes are in Swedish.

**The genealogist · church records (DDS)**
→ A farmer (*gårdsman*) at Horsaryd who died of cholera on 25 September 1834 – one of 38 in the parish that autumn. His birth and marriage are not in the register: the next step is the household examination rolls (*husförhörslängder*).
(Death register, Asarum parish, SE/LLA/13008 – [church book image](https://sok.riksarkivet.se/bildvisning/C0056836_00001). Asarum was hit again in autumn 1857, with 58 deaths. Note: two children in 1899 have the cause of death *kolerin* – usually an acute gastrointestinal illness in children, not Asiatic cholera, even though the register normalises it to “cholera”. A good example of why you check against the original.)

**The researcher · transcribed handwriting**
→ Three perspectives:
- The disease as a threat – guards against seafarers from infected places (SE/HLA/1070112/B/B I/1, pp. 195–196)
- The disease as a cause of death – a widow in Vadstena who died on 22 August 1834 (SE/VaLA/03825/01/A II/205, pp. 385, 387)
- Prisoners at Stockholm’s cholera cemeteries – Svea Court of Appeal, 12 January 1835 (SE/RA/420422/01/A I b 1/118, p. 36) – [original page](https://sok.riksarkivet.se/bildvisning/40006243_00036)

*Follow-up* → The AI’s suggestions, not facts from the source: how were the prisoners used during the epidemic? (In the session it also suggested looking further in the records of the Palace Court (*Slottsrätten*), the prison rolls and the archive of the Board of Health (*Sundhetskollegium*).)

**The archivist · where is the material?**
→ The AI searches using the historical terms in the sources (*lappmark*, *lappman*) and shows that the hits cluster in:
- The Lapland court records 1689–1729, Ume, Lule, Pite and Torne lappmark (SE/HLA/1040125, SE/HLA/1040161) – e.g. a reindeer case from 1706, [original page](https://sok.riksarkivet.se/bildvisning/H0000333_00021)
- Minutes and appeals of the Svea Court of Appeal, 17th century–1830s (SE/RA/420422/01)
- Mining administration records on the silver works and mines in Lule and Torne lappmark, 1740–1851 (SE/HLA/1270004, Board of Mines SE/RA/420013/02)
- Proclamations and letters concerning the Lapland districts, 1673–1793 (SE/HLA/1090014)

**Note:** *Lapmans Rätten* in the Svea Court of Appeal minutes from the 1830s is usually *lagmansrätten* (the lagman’s court) – an HTR misreading. The terms *lapp* and *lappman* are the historical Swedish terms used in the sources; we search for them to find the material, not because they are appropriate terms today. The term today is Sámi (Swedish *samer*).

> **Speaker notes (60 s):**
> Three users, three questions – all tested against this release. Ask them live, in English: that in itself shows the language point. The genealogist asks broadly about an ancestor. Expected: a farmer at Horsaryd who died of cholera on 25 September 1834 – one of 38 in the parish that autumn. His birth and marriage are not in the register, so the next step is the household examination rolls. The point: the AI gives context and is honest about what is missing. The researcher asks about the same epidemic in the handwritten records. Expected: the disease as a threat, as a cause of death, and prisoners working at Stockholm’s cholera cemeteries in 1835 – with a link to each page. The follow-up gives the AI’s own suggestions, not facts from the source – a good moment to talk about source criticism. The archivist wants to know where Sámi material can be found. The AI searches using the historical Swedish terms in the sources, such as “lappmark” and “lappman” – not because they are the right terms today, but because that is how the material is described. Expected: the Lapland court records around 1700, the Svea Court of Appeal, mining administration records and county proclamations.

---

## Slide 4 – How to connect

**Address:** `https://riksarkivet-ra-mcp.hf.space/mcp`

**Login:** None for RA-MCP – the server is open. Your AI assistant does need its own account, often a paid plan.

**Three steps – the same in Claude, ChatGPT, Mistral and others**
1. **Open connectors** – in your AI assistant’s settings: Connectors, Integrations or similar
2. **Add RA-MCP** – choose “Add custom connector”, name it RA-MCP and paste the address
3. **Turn it on and ask** – enable RA-MCP in the chat and try: “Who was Marie Louise Gagner?”

Image: a neutral “Add custom connector” dialog with the fields Name (RA-MCP) and Server address. No accounts, keys or personal data.

> **Speaker notes (60 s):**
> Connecting looks the same in every AI assistant that supports MCP – Claude, ChatGPT, Mistral and others. All you need is the address at the top. RA-MCP requires no login, the server is open, but you need an account with your AI assistant, often a paid plan. Three steps: go to the settings and look for Connectors or Integrations – the name varies a little between services. Choose to add a custom connector, call it RA-MCP and paste the address. Then turn it on in the chat. It takes half a minute. Try a simple question, for example “Who was Marie Louise Gagner?”. If you get an answer with a link to the Swedish Biographical Lexicon, you are connected.

---

## Slide 5 – Status, limits and contact

**Beta test autumn 2026**
- Open beta since September, running until year end
- We learn from the survey, interviews and anonymised logs
- Performance may vary – the server runs on Hugging Face

**Not working yet**
- On-demand HTR (`htr_transcribe`) is switched off on the open server
- Export to Label Studio (`label`) is switched off
- Not all sources are connected – the AI can’t see what’s missing
- Transcribed text is mainly 17th–18th-century court records – not church records or estate inventories (catalogued and often digitised, but not transcribed)
- An empty answer doesn’t mean nothing exists – ask “where did you search?”

**Report and follow**
- Bugs and requests: [AI@riksarkivet.se](mailto:AI@riksarkivet.se)
- Evaluate your testing: [the survey – Beta Test Survey: the Swedish National Archives MCP Server](https://members.paloma.se/Surveys/Pass/ViewSurvey.aspx?survey=57dab472-66f9-425f-883b-3ca43a947dbd)
- Documentation: [ai-riksarkivet.github.io/ra-mcp](https://ai-riksarkivet.github.io/ra-mcp/)

> **Speaker notes (60 s):**
> RA-MCP is a beta, from September to the end of the year. It is limited, it has bugs, and assistants can misread and misquote. It also runs on infrastructure that is not our own – which is why it is a test and not a service. The point is to test early: it is the cheapest way to find out what fails and the fastest way to learn what is worth building. Be honest about the limits, it builds trust. On-demand transcription and the Label Studio export are switched off, and not all sources are connected. Most important: an empty answer doesn’t mean nothing exists – teach the audience to ask “where did you search?” and to check against the original. Bugs and requests go to AI@riksarkivet.se. If you have tested it, please fill in the survey – it shapes what we build next. The documentation is on GitHub.

---

## Questions you may get

Background for the presenter – not shown on the slides.

**Are we handing our material over to the AI companies?**
No. The assistant can query our systems and gets answers back with references. No copy of the collections leaves the archive. But the part of the material an answer is based on does pass through the assistant and is interpreted there.

**How much can the AI actually read?**
Three levels: the catalogue (250,000 finding aids and 2 million+ other records, including undigitised material), digitised images (about 73 million pages that can be viewed) and AI-transcribed text (about 1.6 million pages that can be searched, mainly 17th- and 18th-century court records). What exists only as an image, the AI can show but not search.

**How do I know the answer is right?**
You don’t until you have checked. A document can be authentic while its transcription contains errors (cf. *Lapmans Rätten* = *lagmansrätten*). Follow the reference code to the original, and ask the assistant where it searched, with which words and in which sources.

**Does the AI really follow your instructions on citation?**
Skills and tool descriptions steer the assistant towards citing and not making things up, but that is no guarantee. That is why checking against the original is always the last step.

**What does an empty answer mean?**
Either nothing exists, or the material is in a source that is not connected, not transcribed, or outside the source’s time span and geography. The form of the search terms matters too: historical place names and spellings give different hits than modern ones.

**Do I need to read Swedish?**
No – the assistant translates both ways. But the sources are in Swedish (and older ones in early modern Swedish or Latin), so for anything you will cite or rely on, have the original checked by someone who reads it.

**Why does it run on Hugging Face and not your own infrastructure?**
Because it is a test. Testing early on existing infrastructure is the cheapest way to learn what works and at what scale we need to build our own.
