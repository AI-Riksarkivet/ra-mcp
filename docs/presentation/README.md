---
titel: RA-MCP på fem slides
ägare: AI-labb och datatjänster, Riksarkivet
uppdaterad: 2026-10-14
gäller release: betaversionen hösten 2026 (servern på Hugging Face)
---

# RA-MCP på fem slides

Gemensamt underlag för alla som presenterar RA-MCP – internt eller externt. Texten här är källan; PowerPoint-filen `RA-MCP_HT2026.pptx` ligger i samma mapp och hålls i synk med den – ändra båda samtidigt. En engelsk version finns i `README_EN.md` och `RA-MCP_HT2026_EN.pptx` – uppdatera den också.

**Vid varje release:** kör om exempelfrågorna på slide 3 mot den nya versionen och uppdatera de förväntade svaren, kontrollera modulerna på slide 2 och adressen och gränserna på slide 4–5, uppdatera datumet ovan och i PowerPoint-filen. Varje slide har en talarnotering på ca 60 sekunder.

---

## Slide 1 – Vad är RA-MCP?

**MCP (Model Context Protocol)** är en öppen standard som låter en AI-assistent använda externa verktyg och datakällor.

**RA-MCP** gör Riksarkivets källor till sådana verktyg – fråga på valfritt språk i t.ex. Claude, ChatGPT eller Mistral.

Bild: **Du** (ställer en fråga på valfritt språk – svenska, engelska, finska …) → **AI-assistenten** (tolkar frågan, väljer verktyg och söker på svenska – även äldre stavningar) → **RA-MCP** (frågar våra system – datan stannar hos oss, ingen kopia lämnar arkivet) → **Våra källor** (arkivförteckningar för 250 000 arkiv, 73 miljoner bilder, transkriberad handskrift och 30+ register).

Fotnot: Språket kommer från språkmodellen – svaret kommer tillbaka på ditt språk, med referenser till originalen.

> **Talarnotering (60 s):**
> Varför bryr vi oss? Allt fler når information via en AI-assistent i stället för via ett sökgränssnitt – och det sker oavsett om arkiven förbereder sig. Vi vill finnas där frågorna ställs. MCP är en öppen standard som låter en AI-assistent använda verktyg utanför sig själv. RA-MCP gör våra arkivförteckningar, 73 miljoner bilder, transkriberad handskrift och ett trettiotal register till sådana verktyg. Följ bilden: du frågar på vilket språk du vill. Assistenten väljer verktyg och söker på svenska, gärna med äldre stavningar. Svaret kommer tillbaka på ditt språk, med länkar till originalen. Du behöver inte veta vilken databas som har svaret. Och viktigt för ett arkiv: datan stannar hos oss. Assistenten får ställa frågor, men ingen kopia lämnar arkivet. Samma princip skulle kunna fungera mellan flera institutioner. Eftersom MCP är en standard binder vi oss inte heller vid en leverantör – Claude, ChatGPT och Mistral fungerar alla.

---

## Slide 2 – Vad finns i RA-MCP?

Åtta kort:
- **Sök i handskrift** – AI-transkriberad text, även gamla stavningar
- **Sök i katalogen** – 250 000 arkivförteckningar och 2 miljoner+ andra poster
- **Visa originalen** – bläddra sidor och öppna bilden med texten ovanpå
- **Personer** – födda, döda, vigda och biografiskt lexikon
- **Medeltid** – Svenskt Diplomatariums huvudkartotek (SDHK) och medeltida pergamentomslag (MPO)
- **Fler register** – sjömanshus, domböcker, bolag, fordon m.fl.
- **Forskarguider** – Riksarkivets PDF-guider om källor och arkivhistoria
- **Skills** (framhävt) – inbyggd vägledning som lär AI:n att söka i arkiv

Fotnot: Ett trettiotal sökbara källor – och AI:n väljer själv vilka den behöver för din fråga.

Skills i detalj: åtta inbyggda guider (`archive-search`, `archive-research`, `archival-guide`, `htr-transcription`, `view-document-guide`, `pdf-guide`, `upload-files`, `feedback-ls`).
  *För presentatören:* I Claude (claude.ai, Desktop, VS Code) följer skills med automatiskt som MCP-resurser när man kopplar upp servern. I Claude Code installeras de som pluginet `ra-mcp-tools`. Hur ChatGPT och Mistral använder dem är inte dokumenterat – säg inte att de fungerar där förrän det är testat. `htr-transcription` och `feedback-ls` hör till funktioner som är avstängda i den öppna servern.

> **Talarnotering (60 s):**
> Här är det som finns bakom RA-MCP. Kärnan är tre saker: sökning i AI-transkriberad handskrift, sökning i katalogen, och möjligheten att öppna originalbilden med texten ovanpå. Runt det finns ett trettiotal register – kyrkböckernas födda, döda och vigda, Svenskt biografiskt lexikon, medeltida brev, sjömanshus, domböcker och fler. Det mörka kortet är skills. Det är inbyggd vägledning som lär AI:n hur man söker i arkiv – gamla stavningar, felläst handskrift, rätt källhänvisning. Det är skillnaden mellan att söka och att söka bra, och man behöver inte installera något extra. Poängen: du behöver inte veta vilken källa som har svaret. AI:n väljer själv.

---

## Slide 3 – Vad kan man fråga?

Tre användare – bara frågorna visas på sliden; svaren kommer i demon. Frågorna är testade mot releasen 14 oktober 2026.

- **Släktforskaren · kyrkböckerna (DDS):** ”Vad kan du hitta om min anfader Mathis Michaelsson i Asarum?”
- **Forskaren · transkriberad handskrift:** ”Kan du hitta historiska vittnesmål om koleraepidemin 1834, jämföra hur sjukdomen beskrevs i olika handlingar och visa de originalkällor som ligger bakom dina slutsatser?” – *Följdfråga:* ”Vilka nya forskningsfrågor väcker den här handlingen, och vilket ytterligare arkivmaterial skulle jag behöva undersöka?”
- **Arkivarien · var finns materialet?:** ”Kan du söka fram material med samisk relevans i Riksarkivets HTR:ade arkiv?”

### Förväntade svar (för presentatören – visas inte på sliden)

**Släktforskaren · kyrkböckerna (DDS)**
*”Vad kan du hitta om min anfader Mathis Michaelsson i Asarum?”*
→ Gårdsman i Horsaryd, död i kolera 25 september 1834 – en av 38 i socknen den hösten. Födelse och vigsel finns inte i registret: nästa steg är husförhörslängden.
(Dödbok, Asarums församling, SE/LLA/13008 – [kyrkboksbilden](https://sok.riksarkivet.se/bildvisning/C0056836_00001). Asarum drabbades igen hösten 1857 med 58 döda. Obs: två barn 1899 står med dödsorsaken ”kolerin” – i regel en akut mag-tarmsjukdom hos barn, inte asiatisk kolera, trots att registret normaliserar det till ”kolera”. Bra exempel på att kontrollera mot originalet.)

**Forskaren · transkriberad handskrift**
*”Kan du hitta historiska vittnesmål om koleraepidemin 1834, jämföra hur sjukdomen beskrevs i olika handlingar och visa de originalkällor som ligger bakom dina slutsatser?”*
→ Tre perspektiv:
- Smittan som hot – vakter mot sjöfarande från smittade orter (SE/HLA/1070112/B/B I/1, s. 195–196)
- Farsoten som dödsorsak – en änka i Vadstena död 22 augusti 1834 (SE/VaLA/03825/01/A II/205, s. 385, 387)
- Fångar på Stockholms kolerakyrkogårdar – Svea hovrätt 12 januari 1835 (SE/RA/420422/01/A I b 1/118, s. 36) – [originalsidan](https://sok.riksarkivet.se/bildvisning/40006243_00036)

*Följdfråga: ”Vilka nya forskningsfrågor väcker den här handlingen, och vilket ytterligare arkivmaterial skulle jag behöva undersöka?”*
→ AI:ns förslag, inte fakta i källan: hur användes fångarna under epidemin? (I sessionen föreslog den också att gå vidare i Slottsrättens protokoll, fångrullorna och Sundhetskollegiets arkiv.)

**Arkivarien · var finns materialet?**
*”Kan du söka fram material med samisk relevans i Riksarkivets HTR:ade arkiv?”*
→ AI:n söker på källornas historiska termer (”lappmark”, ”lappman”) och visar att träffarna samlas i:
- Lappmarkernas domböcker 1689–1729, Ume, Lule, Pite och Torne lappmark (SE/HLA/1040125, SE/HLA/1040161) – t.ex. ett renmål 1706, [originalsidan](https://sok.riksarkivet.se/bildvisning/H0000333_00021)
- Svea hovrätts protokoll och besvär, 1600-tal–1830-tal (SE/RA/420422/01)
- Bergsväsendets akter om silververken och gruvorna i Lule och Torne lappmark, 1740–1851 (SE/HLA/1270004, Bergskollegium SE/RA/420013/02)
- Kungörelser och skrivelser om lappmarkerna, 1673–1793 (SE/HLA/1090014)

**Obs:** ”Lapmans Rätten” i Svea hovrätts protokoll från 1830-talet är oftast *lagmansrätten* – ett HTR-fel. Termerna ”lapp” och ”lappman” är källornas historiska benämningar; vi söker på dem för att hitta materialet, inte för att de är rätt benämning i dag.

> **Talarnotering (60 s):**
> Tre användare, tre frågor – alla testade mot den här releasen. Ställ dem live. Släktforskaren frågar brett om en anfader. Förväntat: gårdsman i Horsaryd, död i kolera 25 september 1834 – en av 38 i socknen den hösten. Födelse och vigsel finns inte i registret, så nästa steg är husförhörslängden. Poängen: AI:n ger sammanhang och säger ärligt vad som saknas. Forskaren frågar om samma epidemi i handskriften. Förväntat: smittan som hot, som dödsorsak och fångar på Stockholms kolerakyrkogårdar 1835 – med länk till varje sida. Följdfrågan ger AI:ns egna förslag, inte fakta i källan – ett bra tillfälle att prata källkritik. Arkivarien vill veta var samiskt material finns. AI:n söker på källornas historiska termer, som ”lappmark” och ”lappman” – inte för att det är rätt benämning i dag, utan för att det är så materialet är beskrivet. Förväntat: lappmarkernas domböcker kring 1700, Svea hovrätt, bergsväsendet och länets kungörelser.

---

## Slide 4 – Så kopplar du upp dig

**Adress:** `https://riksarkivet-ra-mcp.hf.space/mcp`

**Inloggning:** Ingen inloggning mot RA-MCP – servern är öppen. Däremot kräver din AI-assistent ett eget konto, ofta en betald plan.

**Tre steg – likadant i Claude, ChatGPT, Mistral m.fl.**
1. **Öppna anslutningarna** – i din AI-assistents inställningar: Anslutningar, Connectors eller Integrationer
2. **Lägg till RA-MCP** – välj ”Lägg till anpassad anslutning”, skriv namnet RA-MCP och klistra in adressen
3. **Slå på och fråga** – aktivera RA-MCP i chatten och testa: ”Vem var Marie Louise Gagner?”

Bild: en neutral dialogruta ”Lägg till anpassad anslutning” med fälten Namn (RA-MCP) och Serverns adress. Inga konton, nycklar eller personuppgifter.

> **Talarnotering (60 s):**
> Att koppla upp sig ser likadant ut i alla AI-assistenter som stöder MCP – Claude, ChatGPT, Mistral och flera andra. Det enda man behöver är adressen högst upp. RA-MCP kräver ingen inloggning, servern är öppen, men man behöver ett konto i sin AI-assistent, och ofta en betald plan. Tre steg: gå till inställningarna och leta efter Anslutningar, Connectors eller Integrationer – namnet skiljer sig lite mellan tjänsterna. Välj att lägga till en anpassad anslutning, kalla den RA-MCP och klistra in adressen. Slå sedan på den i chatten. Det tar en halv minut. Testa med en enkel fråga, till exempel ”Vem var Marie Louise Gagner?”. Får ni ett svar med en länk till Svenskt biografiskt lexikon är ni uppkopplade.

---

## Slide 5 – Status, gränser och kontakt

**Betatest – hösten 2026**
- Öppen beta sedan september, pågår året ut
- Vi lär oss av enkäten, intervjuer och anonymiserade loggar
- Prestanda kan vara ojämn; servern ligger på Hugging Face

**Fungerar inte än**
- HTR på begäran (`htr_transcribe`) är avstängd i den öppna servern
- Exporten till Label Studio (`label`) är avstängd
- Alla källor är inte kopplade – det som inte är kopplat ser AI:n inte
- Transkriberad text finns främst för domstolsmaterial 1600–1700-tal – inte för kyrkböcker eller bouppteckningar (katalogiserade och ofta digitaliserade, men inte transkriberade)
- Tomt svar betyder inte att något saknas – fråga ”var har du sökt?”

**Rapportera och följ**
- Fel och önskemål: [AI@riksarkivet.se](mailto:AI@riksarkivet.se)
- Utvärdera din testning: [enkäten – Beta Test Survey: the Swedish National Archives MCP Server](https://members.paloma.se/Surveys/Pass/ViewSurvey.aspx?survey=57dab472-66f9-425f-883b-3ca43a947dbd)
- Dokumentation: [ai-riksarkivet.github.io/ra-mcp](https://ai-riksarkivet.github.io/ra-mcp/)

> **Talarnotering (60 s):**
> RA-MCP är en beta, från september året ut. Den är begränsad, har buggar, och assistenterna kan läsa och citera fel. Den körs dessutom på infrastruktur som inte är vår egen – därför är det ett test och inte en tjänst. Poängen är att testa tidigt: det är det billigaste sättet att hitta vad som inte fungerar och det snabbaste sättet att lära oss vad som är värt att bygga. Var ärlig om gränserna, det bygger förtroende. Transkribering på begäran och exporten till Label Studio är avstängda, och alla källor är inte kopplade. Viktigast: ett tomt svar betyder inte att något saknas – lär publiken att fråga ”var har du sökt?” och att kontrollera mot originalet. Fel och önskemål skickar man till AI@riksarkivet.se. Har man testat, fyll i enkäten – den styr vad vi bygger härnäst. Dokumentationen finns på GitHub.

---

## Frågor ni kan få

Bakgrund för den som presenterar – visas inte på sliderna.

**Lämnar vi ut vårt material till AI-bolagen?**
Nej. Assistenten får ställa frågor till våra system och får tillbaka svar med referenser. Ingen kopia av samlingarna lämnar arkivet. Men den del av materialet som ett svar bygger på passerar genom assistenten och tolkas där.

**Hur mycket kan AI:n faktiskt läsa?**
Tre nivåer: katalogen (250 000 arkivförteckningar och 2 miljoner+ andra poster, även odigitaliserat), digitaliserade bilder (cirka 73 miljoner sidor som går att visa) och AI-transkriberad text (cirka 1,6 miljoner sidor som går att söka i, främst domstolsmaterial från 1600- och 1700-talen). Det som bara finns som bild kan AI:n visa men inte söka i.

**Hur vet jag att svaret stämmer?**
Det vet man inte förrän man kontrollerat. Ett dokument kan vara äkta medan transkriberingen innehåller fel (jfr ”Lapmans Rätten” = lagmansrätten). Följ referenskoden till originalet och fråga assistenten var den har sökt, med vilka ord och i vilka källor.

**Följer AI:n verkligen era instruktioner om källhänvisning?**
Skills och verktygsbeskrivningar styr assistenten mot att citera och inte hitta på, men det är ingen garanti. Därför är kontroll mot originalet alltid sista steget.

**Vad betyder ett tomt svar?**
Antingen finns inget, eller så finns materialet i en källa som inte är kopplad, inte transkriberad eller ligger utanför källans tidsram och geografi. Sökordens form spelar också roll: historiska ortnamn och stavningar ger andra träffar än moderna.

**Varför kör ni det på Hugging Face och inte på egen infrastruktur?**
För att det är ett test. Att testa tidigt på befintlig infrastruktur är det billigaste sättet att lära sig vad som fungerar och i vilken skala vi behöver bygga eget.

