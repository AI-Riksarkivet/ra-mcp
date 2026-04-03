<script lang="ts">
import { onMount } from "svelte";
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";

interface SBLArticle {
  article_id: number;
  surname: string;
  given_name: string;
  gender: string;
  article_type: string;
  occupation: string;
  birth_year: number | null;
  birth_month: number | null;
  birth_day: number | null;
  birth_place: string;
  birth_place_comment: string;
  death_year: number | null;
  death_month: number | null;
  death_day: number | null;
  death_place: string;
  death_place_comment: string;
  cv: string;
  archive: string;
  printed_works: string;
  sources: string;
  article_author: string;
  volume_number: string;
  page_number: string;
  sbl_uri: string;
  image_files: string[];
  image_descriptions: string[];
}

type Tab = "om" | "meriter" | "tryckta" | "kallor" | "arkiv";

let app = $state<App | null>(null);
let hostContext = $state<McpUiHostContext | undefined>();
let article = $state<SBLArticle | null>(null);
let error = $state<string | null>(null);
let isLoading = $state(false);
let history = $state<number[]>([]);
let activeTab = $state<Tab>("meriter");
let viewId = $state("");
let pollTimer: ReturnType<typeof setInterval> | null = null;

function isFamily(a: SBLArticle): boolean {
  return a.article_type === "Family article" || a.given_name === "släkt";
}

function displayName(a: SBLArticle): string {
  if (isFamily(a)) return `Släkten ${a.surname}`;
  return `${a.given_name} ${a.surname}`.trim();
}

function availableTabs(a: SBLArticle): { id: Tab; label: string }[] {
  const tabs: { id: Tab; label: string }[] = [{ id: "om", label: "Om" }];
  if (a.cv) tabs.push({ id: "meriter", label: "Meriter" });
  if (a.printed_works) tabs.push({ id: "tryckta", label: "Tryckta arbeten" });
  if (a.sources) tabs.push({ id: "kallor", label: "Källor" });
  if (a.archive) tabs.push({ id: "arkiv", label: "Arkiv" });
  return tabs;
}

function tabContent(a: SBLArticle, tab: Tab): string {
  if (tab === "meriter") return a.cv || "";
  if (tab === "tryckta") return a.printed_works || "";
  if (tab === "kallor") return a.sources || "";
  if (tab === "arkiv") return a.archive || "";
  return "";
}

function formatDate(year: number | null, month: number | null, day: number | null): string {
  if (!year) return "";
  const parts: string[] = [];
  if (day) parts.push(String(day));
  if (month) {
    const months = [
      "januari", "februari", "mars", "april", "maj", "juni",
      "juli", "augusti", "september", "oktober", "november", "december",
    ];
    parts.push(months[month - 1] ?? String(month));
  }
  parts.push(String(year));
  return parts.join(" ");
}

function formatLifespan(a: SBLArticle): string {
  const birth = formatDate(a.birth_year, a.birth_month, a.birth_day);
  const death = formatDate(a.death_year, a.death_month, a.death_day);
  if (!birth && !death) return "";
  if (birth && !death) return `f. ${birth}`;
  if (!birth && death) return `d. ${death}`;
  return `${birth}\u2013${death}`;
}

function formatSBLText(text: string): string {
  if (!text) return "";
  let html = text;

  html = html.replace(/<span[^>]*>\s*<\/span>/g, "");
  for (let i = 0; i < 5; i++) {
    html = html.replace(/<span[^>]*>\s*<\/span>/g, "");
  }

  html = html.replace(
    /<a\s+href="[^"]*?id(?:&#x3D;|=)(\d+)[^"]*"[^>]*>(.*?)<\/a>/gi,
    '<a href="#" data-article-id="$1" class="sbl-ref">$2</a>'
  );

  html = html.replace(
    /\[a:(\d+):([^\]]+)\]/g,
    '<a href="#" data-article-id="$1" class="sbl-ref">$2</a>'
  );

  html = html.replace(/&minus;/g, "\u2013");
  html = html.replace(/<(?!\/?a[\s>]|\/?abbr[\s>])[^>]+>/g, "");

  const abbrevs: [RegExp, string][] = [
    [/\bf\b(?=\s+\d)/g, "född"],
    [/\bd\b(?=\s+\d)/g, "död"],
    [/\bG\b(?=\s+\d)/g, "Gift"],
    [/\btrol\b/g, "troligen"],
    [/\bdvs\b/g, "det vill säga"],
    [/\bbl\s*a\b/g, "bland annat"],
    [/\bs\s*å\b/g, "samma år"],
    [/\bs\s*d\b/g, "samma dag"],
    [/\bSthlm\b/g, "Stockholm"],
    [/\bSth\b/g, "Stockholm"],
    [/\bGbg\b/g, "Göteborg"],
    [/\bsn\b/g, "socken"],
    [/\bhd\b/g, "härad"],
    [/\bfors\b/g, "församling"],
    [/\bförs\b/g, "församling"],
    [/\buniv\b/g, "universitet"],
    [/\bprof\b/g, "professor"],
    [/\bdoc\b/g, "docent"],
    [/\btf\b/g, "tillförordnad"],
    [/\bbitr\b/g, "biträdande"],
    [/\be\s*o\b/g, "extra ordinarie"],
    [/\bkh\b/g, "kyrkoherde"],
    [/\bkpl\b/g, "kapellan"],
    [/\bRA\b/g, "Riksarkivet"],
    [/\bKB\b/g, "Kungliga biblioteket"],
    [/\bUU\b/g, "Uppsala universitet"],
    [/\bLU\b/g, "Lunds universitet"],
    [/\bLVA\b/g, "Ledamot av Vetenskapsakademien"],
    [/\bRSO\b/g, "Riddare av Svärdsorden"],
    [/\bKSO\b/g, "Kommendör av Svärdsorden"],
    [/\bRNO\b/g, "Riddare av Nordstjärneorden"],
    [/\bKNO\b/g, "Kommendör av Nordstjärneorden"],
  ];

  for (const [pattern, expansion] of abbrevs) {
    html = html.replace(pattern, (match) =>
      `<abbr title="${expansion}">${match}</abbr>`
    );
  }

  return html;
}

function handleArticleClick(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const link = target.closest('a[data-article-id]') as HTMLAnchorElement | null;
  if (!link) return;
  e.preventDefault();
  const id = parseInt(link.dataset.articleId!, 10);
  if (id && app) loadArticle(id);
}

async function loadArticle(articleId: number) {
  isLoading = true;
  error = null;
  try {
    const result = await app!.callServerTool({
      name: "load_sbl_article",
      arguments: { article_id: articleId, view_id: viewId },
    });
    if (result.structuredContent) {
      article = result.structuredContent as SBLArticle;
      history.push(articleId);
      activeTab = "om";
    }
    isLoading = false;
  } catch (err: any) {
    error = err.message;
    isLoading = false;
  }
}

function goBack() {
  if (history.length < 2) return;
  history.pop();
  const prevId = history[history.length - 1];
  loadArticle(prevId);
}

function startPolling() {
  pollTimer = setInterval(async () => {
    if (!app) return;
    try {
      if (!viewId) return;
      const result = await app.callServerTool({
        name: "get_sbl_state",
        arguments: { view_id: viewId },
      });
      const sc = result.structuredContent as SBLArticle | undefined;
      if (sc && sc.article_id !== article?.article_id) {
        article = sc;
        isLoading = false;
        history.push(sc.article_id);
        activeTab = "om";
      }
    } catch {}
  }, 3000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

$effect(() => {
  if (hostContext?.theme) applyDocumentTheme(hostContext.theme);
  if (hostContext?.styles?.variables) applyHostStyleVariables(hostContext.styles.variables);
  if (hostContext?.styles?.css?.fonts) applyHostFonts(hostContext.styles.css.fonts);
});


onMount(async () => {
  const instance = new App(
    { name: "SBL Article Viewer", version: "1.0.0" },
    { availableDisplayModes: ["inline"] },
    { autoResize: true },
  );

  instance.ontoolinputpartial = () => { if (!article) isLoading = true; };
  instance.ontoolinput = () => { isLoading = true; error = null; };
  instance.ontoolresult = (result) => {
    isLoading = false;
    if (result.isError) {
      error = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Unknown error";
      return;
    }
    const sc = result.structuredContent as (SBLArticle & { view_id?: string }) | undefined;
    if (sc) {
      if (sc.view_id) viewId = sc.view_id;
      article = sc; error = null; history.push(sc.article_id); activeTab = "om";
    }
  };
  instance.ontoolcancelled = () => { isLoading = false; };
  instance.onerror = (err) => { console.error("App error:", err); error = err.message; };
  instance.onhostcontextchanged = (params) => { hostContext = { ...hostContext, ...params }; };
  instance.onteardown = async () => { stopPolling(); return {}; };

  await instance.connect();
  app = instance;
  hostContext = instance.getHostContext();
  startPolling();
});
</script>

<main>
  {#if error}
    <div class="state-msg error"><p>{error}</p></div>
  {:else if isLoading}
    <div class="state-msg"><p>Laddar artikel...</p></div>
  {:else if !article}
    <div class="state-msg"><p>Väntar på artikeldata...</p></div>
  {:else}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div class="card" onclick={handleArticleClick}>
      <!-- Title bar: compact name + back button -->
      <div class="title-bar">
        {#if history.length >= 2}
          <button class="back-btn" onclick={(e) => { e.stopPropagation(); goBack(); }}>&larr;</button>
        {/if}
        <span class="title-name">{displayName(article)}</span>
        {#if isFamily(article)}
          <span class="title-occ">Släktartikel</span>
        {:else if article.occupation}
          <span class="title-occ">{article.occupation}</span>
        {/if}
      </div>

      {#if isFamily(article) && !article.cv && !article.printed_works && !article.archive}
        <!-- Family article: compact inline view, no tabs -->
        <div class="tab-content">
          <div class="about-info">
            <p class="ref" style="margin-bottom: 0.5rem">SBL band {article.volume_number}, s. {article.page_number}</p>
            {#if article.sources}
              <p class="section-label">Källor och litteratur</p>
              <div class="content pre-wrap">{@html formatSBLText(article.sources)}</div>
            {/if}
            <div class="about-links" style="margin-top: 0.5rem">
              {#if article.article_author}
                <span class="author">{article.article_author}</span>
              {/if}
              {#if article.sbl_uri}
                <a href={article.sbl_uri} target="_blank" rel="noopener noreferrer">Läs på SBL →</a>
              {/if}
            </div>
          </div>
        </div>
      {:else}
        <!-- Person article (or family with content): tabbed view -->
        <nav class="tabs">
          {#each availableTabs(article) as tab}
            <button
              class="tab"
              class:active={activeTab === tab.id}
              onclick={() => { activeTab = tab.id; }}
            >{tab.label}</button>
          {/each}
        </nav>

        <div class="tab-content">
          {#if activeTab === "om"}
            <div class="about-panel">
              {#if Array.isArray(article.image_files) && article.image_files.length > 0}
                <img class="portrait" src={article.image_files[0]}
                  alt={article.image_descriptions?.[0] ?? displayName(article)} />
              {/if}
              <div class="about-info">
                <h1>{displayName(article)}</h1>
                {#if isFamily(article)}
                  <p class="occupation">Släktartikel</p>
                {:else if article.occupation}
                  <p class="occupation">{article.occupation}</p>
                {/if}
                {#if !isFamily(article) && formatLifespan(article)}
                  <p class="lifespan">{formatLifespan(article)}</p>
                {/if}
                {#if !isFamily(article) && (article.birth_place || article.death_place)}
                  <p class="places">
                    {#if article.birth_place}
                      <span>f. {article.birth_place}{#if article.birth_place_comment} ({article.birth_place_comment}){/if}</span>
                    {/if}
                    {#if article.birth_place && article.death_place}
                      <span class="sep"> · </span>
                    {/if}
                    {#if article.death_place}
                      <span>d. {article.death_place}{#if article.death_place_comment} ({article.death_place_comment}){/if}</span>
                    {/if}
                  </p>
                {/if}
                {#if article.volume_number || article.page_number}
                  <p class="ref">SBL band {article.volume_number}, s. {article.page_number}</p>
                {/if}
                <div class="about-links">
                  {#if article.article_author}
                    <span class="author">{article.article_author}</span>
                  {/if}
                  {#if article.sbl_uri}
                    <a href={article.sbl_uri} target="_blank" rel="noopener noreferrer">Läs på SBL →</a>
                  {/if}
                  <a href="https://sok.riksarkivet.se/sbl/Hjalp.aspx" target="_blank" rel="noopener noreferrer">Förkortningar</a>
                </div>
              </div>
            </div>
          {:else}
            <div class="content pre-wrap">{@html formatSBLText(tabContent(article, activeTab))}</div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</main>

<style>
  main {
    font-family: inherit;
    line-height: 1.5;
    padding: 0.5rem;
  }

  .state-msg {
    display: flex; align-items: center; justify-content: center;
    min-height: 100px; opacity: 0.7; font-size: 0.9rem;
  }
  .error { color: #dc2626; }

  .card {
    border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
    border-radius: 8px;
    overflow: hidden;
  }

  /* Title bar */
  .title-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }
  .title-name { font-weight: 600; }
  .title-occ { opacity: 0.6; font-style: italic; }

  .back-btn {
    padding: 0.1rem 0.4rem;
    font-size: 0.8rem;
    color: LinkText;
    background: none;
    border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
    border-radius: 4px;
    cursor: pointer;
    line-height: 1;
  }
  .back-btn:hover { background: color-mix(in srgb, currentColor 5%, transparent); }

  /* Tabs */
  .tabs {
    display: flex;
    border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent);
    border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent);
    overflow-x: auto;
  }

  .tab {
    flex: 1;
    padding: 0.4rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: inherit;
    opacity: 0.6;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    white-space: nowrap;
  }
  .tab:hover { opacity: 0.9; }
  .tab.active {
    opacity: 1;
    color: LinkText;
    border-bottom-color: LinkText;
  }

  /* Tab content */
  .tab-content {
    padding: 0.75rem 1rem;
    max-height: 280px;
    overflow-y: auto;
  }

  /* About panel (Om tab) */
  .about-panel {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }

  .portrait {
    width: 100px;
    height: auto;
    border-radius: 6px;
    flex-shrink: 0;
    object-fit: cover;
  }

  .about-info {
    flex: 1;
    min-width: 0;
  }

  h1 {
    font-size: 1.15rem;
    font-weight: 700;
    line-height: 1.2;
    margin: 0 0 0.15rem;
  }

  .section-label {
    font-size: 0.78rem;
    font-weight: 600;
    opacity: 0.6;
    margin-bottom: 0.3rem;
  }

  .occupation {
    font-size: 0.85rem;
    opacity: 0.7;
    font-style: italic;
    margin: 0 0 0.15rem;
  }

  .lifespan {
    font-size: 0.82rem;
    opacity: 0.7;
    margin: 0 0 0.1rem;
  }

  .places {
    font-size: 0.78rem;
    opacity: 0.5;
    margin: 0 0 0.1rem;
  }
  .sep { opacity: 0.5; }

  .ref {
    font-size: 0.72rem;
    opacity: 0.5;
    margin: 0.3rem 0 0;
  }

  .about-links {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
    font-size: 0.72rem;
    opacity: 0.6;
  }
  .about-links a {
    color: LinkText;
    text-decoration: none;
  }
  .about-links a:hover { text-decoration: underline; }
  .author { font-style: italic; }

  /* Text content */
  .content {
    font-size: 0.85rem;
    line-height: 1.65;
  }

  .pre-wrap {
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* Cross-reference links */
  :global(.sbl-ref) {
    color: LinkText;
    text-decoration: none;
    border-bottom: 1px dotted LinkText;
    cursor: pointer;
  }
  :global(.sbl-ref:hover) { border-bottom-style: solid; }

  /* Abbreviation tooltips */
  :global(abbr[title]) {
    text-decoration: none;
    border-bottom: 1px dotted currentColor;
    opacity: 0.6;
    cursor: help;
  }
  :global(abbr[title]:hover) { opacity: 1; }
</style>
